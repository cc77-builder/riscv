import copy
import unittest
import run_supplements as run


class SeedContractTest(unittest.TestCase):
    def legacy(self):
        return dict(command=['timeout','120m','stdbuf','-o0','-e0','/emu','-i','/image',
                             '--flash=/flash','--ram-size=128MB','--diff=/ref','--max-cycles=5000000'])

    def seeded(self,seed=1):
        value=self.legacy()
        value.update(runtime_contract=run.SEED_CONTRACT,emu_seed=seed)
        value['command'].append(f'--seed={seed}')
        return value

    def test_old_command_keeps_implicit_identity(self):
        value=self.legacy()
        self.assertIsNone(run.validate_seed_command(value,copy.deepcopy(value)))
        value['command'].append('--seed=1')
        with self.assertRaises(ValueError):run.validate_seed_command(value,value)

    def test_explicit_seed_is_bounded_and_exact(self):
        for seed in (1,2147483647):
            value=self.seeded(seed)
            self.assertEqual(run.validate_seed_command(value,copy.deepcopy(value)),seed)
        for seed in (0,-1,2147483648,True,None,'1'):
            with self.subTest(seed=seed),self.assertRaises(ValueError):run.validate_seed(seed)

    def test_command_mutations_rejected(self):
        good=self.seeded()
        mutations=[good['command'][:-1],good['command']+['--seed=1'],
                   good['command'][:-1]+['--seed=2'],good['command'][:-1]+['--seed=01']]
        for command in mutations:
            value=dict(good,command=command)
            with self.subTest(command=command),self.assertRaises(ValueError):
                run.validate_seed_command(value,copy.deepcopy(value))

    def test_runtime_receipt_drift_rejected(self):
        good=self.seeded()
        for changes in (dict(emu_seed=2),dict(emu_seed=True),dict(runtime_contract=None)):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                run.validate_seed_command(good,dict(good,**changes))
        with self.assertRaises(ValueError):run.validate_seed_command(good,self.legacy())

    def test_actual_terminal_seed_required_once(self):
        line='Seed=1 Guest cycle spent: 123 (this will be different from cycleCnt)\n'
        run.validate_seed_log('\x1b[0m'+line,1)
        run.validate_seed_log(line.replace('123','1,234'),1)
        for text in ('',line.replace('Seed=1','Seed=0'),line+line,
                     line+'Seed=2\n',line.replace('Guest cycle spent:','other:')):
            with self.subTest(text=text),self.assertRaises(ValueError):run.validate_seed_log(text,1)

    def test_historical_output_not_relabelled(self):
        run.validate_seed_log('Seed=0 Guest cycle spent: 123 (legacy)\n',None)
        with self.assertRaises(ValueError):
            run.validate_seed_log('Seed=0 Guest cycle spent: 123 (legacy)\n',1)


if __name__=='__main__':unittest.main()
