#!/usr/bin/env python3
"""Offline relation tests; only explicit workspace fixture reads and scratch writes."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import types
import unittest

HERE = Path('line-2/tools/field-relations')
module = types.ModuleType('tested_field_relations')
module.__file__ = str(HERE.absolute() / 'check.py')
exec(compile((HERE / 'check.py').read_bytes(), module.__file__, 'exec'), module.__dict__)

class Memory:
    def __init__(self, files):
        self.files = files
        self.reads = []
    def read_bytes(self, name):
        self.reads.append(name)
        return self.files[name]

class Relations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deps = module.dependencies()

    def check(self, text, rows=None, contract=None, pins=None):
        if isinstance(text, str): text = text.encode('utf-8')
        if rows is None: rows = [{'left':'/a','op':'le','right':'/b'}]
        plan = json.dumps({'relations': rows}).encode()
        if contract is None: contract = {'type':'object'}
        reader = Memory({'c':json.dumps(contract).encode(), 'd':text, 'p':plan})
        result = module.inspect(reader, *self.deps[1:], 'c', 'd', 'p', **(pins or {}))
        return result, reader

    def test_all_operators(self):
        for op, valid in [('eq',False),('ne',True),('lt',True),('le',True),('gt',False),('ge',False)]:
            with self.subTest(op=op):
                r,_=self.check('{"a":2,"b":3}',[{'left':'/a','op':op,'right':'/b'}])
                self.assertEqual(r['valid'],valid)

    def test_equality_boundaries(self):
        for op in ('eq','le','ge'):
            r,_=self.check('{"a":2,"b":2.0}',[{'left':'/a','op':op,'right':'/b'}])
            self.assertTrue(r['valid'])

    def test_decimal_rounding(self):
        r,_=self.check('{"a":9007199254740993.0,"b":9007199254740992.0}')
        self.assertFalse(r['valid'])
        r,_=self.check('{"a":1e-400,"b":0}')
        self.assertFalse(r['valid'])

    def test_typed_equality(self):
        for a,b in [('true','1'),('null','false'),('"1"','1'),('"ZTO"','"IMD"')]:
            r,_=self.check('{"a":'+a+',"b":'+b+'}',[{'left':'/a','op':'eq','right':'/b'}])
            self.assertFalse(r['valid'])
        r,_=self.check('{"a":null,"b":null}',[{'left':'/a','op':'eq','right':'/b'}])
        self.assertTrue(r['valid'])

    def test_ordering_refuses_strings_and_booleans(self):
        for pair in ('"2","3"','true,2','null,2'):
            a,b=pair.split(',')
            r,_=self.check('{"a":'+a+',"b":'+b+'}')
            self.assertEqual(r['relations'][0]['status'],'ordering_requires_numbers')

    def test_missing_deep_and_both_sides(self):
        r,_=self.check('{"a":{}}',[{'left':'/a/no/deep','op':'ne','right':'/other'}])
        row=r['relations'][0]
        self.assertFalse(row['valid'])
        self.assertEqual(row['left']['anchor_pointer'],'/a')
        self.assertEqual(row['right']['anchor_pointer'],'')
        self.assertEqual(set(row['operand_errors']),{'left','right'})
        self.assertNotIn('document_source',row['left'])

    def test_objects_and_arrays_refuse(self):
        for value in ('[]','{}'):
            r,_=self.check('{"a":'+value+',"b":'+value+'}',[{'left':'/a','op':'eq','right':'/b'}])
            self.assertEqual(r['relations'][0]['status'],'invalid_operands')

    def test_escaped_and_array_pointers(self):
        r,_=self.check('{"a/b":{"~":[2,3]}}',[{'left':'/a~1b/~0/0','op':'lt','right':'/a~1b/~0/1'}])
        self.assertTrue(r['valid'])
        r,_=self.check('{"a":[2]}',[{'left':'/a/00','op':'eq','right':'/a/0'}])
        self.assertFalse(r['valid'])

    def test_root(self):
        r,_=self.check('2',[{'left':'','op':'eq','right':''}],{'type':'number'})
        self.assertTrue(r['valid'])

    def test_unicode_crlf_source_ranges(self):
        text='{\r\n "é": "蛙",\r\n "b": "IMD"\r\n}'
        r,_=self.check(text,[{'left':'/é','op':'ne','right':'/b'}])
        span=r['relations'][0]['left']['document_source']['value']
        self.assertEqual(text.encode()[span['start']['byte_offset']:span['end']['byte_offset']], '"蛙"'.encode())
        self.assertEqual(span['start']['line'],2)
        self.assertEqual(span['start']['column'],7)
        self.assertIn('value',r['relations'][0]['plan_source'])

    def test_structure_cannot_be_bypassed(self):
        r,_=self.check('{"a":2,"b":3}',contract={'type':'object','properties':{'a':{'type':'string'}}})
        self.assertFalse(r['valid'])
        self.assertTrue(r['relations'][0]['valid'])
        self.assertEqual(r['structural']['errors'][0]['path'],'/a')

    def test_bad_plans_before_other_reads(self):
        plans=[{}, {'relations':[]}, {'relations':[{}]}, {'relations':[{'left':[],'op':'eq','right':''}]},
               {'relations':[{'left':'/a~2','op':'eq','right':''}]},
               {'relations':[{'left':'a','op':'eq','right':''}]},
               {'relations':[{'left':'','op':'EQ','right':''}]},
               {'relations':[{'left':'','op':'eq','right':'','extra':1}]},
               {'relations':[{'left':'','op':'eq','right':''}]*65}]
        for plan in plans:
            reader=Memory({'p':json.dumps(plan).encode()})
            with self.subTest(plan=plan),self.assertRaises(ValueError):
                module.inspect(reader,*self.deps[1:],'c','d','p')
            self.assertEqual(reader.reads,['p'])

    def test_bad_contract_before_document_read(self):
        reader=Memory({'p':b'{"relations":[{"left":"","op":"eq","right":""}]}','c':b'{"type":"typo"}'})
        with self.assertRaises(ValueError):module.inspect(reader,*self.deps[1:],'c','d','p')
        self.assertEqual(reader.reads,['p','c'])

    def test_malformed_and_ambiguous_json(self):
        for text in ('{"a":2,}', '{"a":2,"a":3}', '{"a":NaN}', '{"a":1e309}'):
            with self.subTest(text=text),self.assertRaises(ValueError):self.check(text)

    def test_pins_and_single_capture(self):
        # Same file can serve all roles when its extra structural rules are absent;
        # demonstrate single capture on contract=document using an object contract.
        contract=b'{"type":"object"}'
        plan=b'{"relations":[{"left":"/type","op":"eq","right":"/type"}]}'
        reader=Memory({'c':contract,'p':plan})
        r=module.inspect(reader,*self.deps[1:],'c','c','p',hashlib.sha256(contract).hexdigest(),hashlib.sha256(contract).hexdigest(),hashlib.sha256(plan).hexdigest())
        self.assertTrue(r['valid']);self.assertEqual(reader.reads,['p','c'])
        for role in ('contract','document','plan'):
            with self.subTest(role=role),self.assertRaises(ValueError):self.check('{"a":1,"b":2}',pins={role+'_sha256':'0'*64})
        with self.assertRaises(ValueError):self.check('{}',pins={'plan_sha256':'wrong'})

    def test_complete_output_bound(self):
        r,_=self.check('{"a":1,"b":2}')
        self.assertTrue(self.deps[2].encode(r).endswith('\n'))
        with self.assertRaises(ValueError):self.deps[2].encode({'x':'x'*100000})

    def test_cli_overflow_has_no_partial_stdout(self):
        from unittest.mock import patch
        pointer='/'+'x'*1023
        plan={'relations':[{'left':pointer,'op':'eq','right':pointer}]*64}
        reader=Memory({'p':json.dumps(plan).encode(),'c':b'{"type":"object"}','d':b'{}'})
        out,err=io.StringIO(),io.StringIO()
        with patch.object(module,'dependencies',return_value=(reader,*self.deps[1:])),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            code=module.main(['c','d','p'])
        self.assertEqual(code,2)
        self.assertEqual(out.getvalue(),'')
        self.assertFalse(json.loads(err.getvalue())['complete'])

    def test_invalid_unselected_field_still_rejects(self):
        contract={'type':'object','properties':{'extra':{'type':'boolean'}}}
        r,_=self.check('{"a":1,"b":2,"extra":"true"}',contract=contract)
        self.assertFalse(r['valid'])
        self.assertTrue(r['relations'][0]['valid'])
        self.assertEqual(r['structural']['errors'][0]['path'],'/extra')

    def test_saved_real_plan_and_reversal(self):
        for filename,valid in [('window-plan.json',True),('reversed-window.json',False)]:
            r=module.inspect(*self.deps,str(HERE/'window.contract.json'),str(HERE/filename),str(HERE/'window.relations.json'))
            self.assertEqual(r['valid'],valid)
            self.assertTrue(r['structural']['valid'])
            self.assertEqual(r['failed_relations'],0 if valid else 1)
        self.assertEqual((HERE/'window-plan.json').read_bytes(),Path('shared/window-settlement/plan.json').read_bytes())

    def test_safe_path_boundary_and_immutability(self):
        base=Path('test/scratch/field-relations');base.mkdir(parents=True,exist_ok=True)
        leaf=base/'safe.json';leaf.write_text('{}')
        link=base/'link.json'
        if link.is_symlink():link.unlink()
        link.symlink_to('safe.json')
        for name in ('../outside','/outside','.hidden',str(link),str(base)):
            with self.subTest(name=name),self.assertRaises((ValueError,OSError)):
                self.deps[0].read_bytes(name)
        self.assertEqual(leaf.read_text(),'{}')
        names=[HERE/n for n in ('window.contract.json','window-plan.json','window.relations.json')]
        before=[p.read_bytes() for p in names]
        module.inspect(*self.deps,*map(str,names[:2]),str(names[2]))
        self.assertEqual(before,[p.read_bytes() for p in names])

    def test_cli_exits_and_all_or_nothing(self):
        args=[str(HERE/'window.contract.json'),str(HERE/'window-plan.json'),str(HERE/'window.relations.json')]
        for document,code in [('window-plan.json',0),('reversed-window.json',1),('absent.json',2)]:
            out,err=io.StringIO(),io.StringIO();args[1]=str(HERE/document)
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):result=module.main(args)
            self.assertEqual(result,code)
            report=json.loads(err.getvalue() if code==2 else out.getvalue())
            self.assertEqual(report['complete'],code!=2)
            if code==2:self.assertEqual(out.getvalue(),'')

if __name__=='__main__':unittest.main(verbosity=2)
