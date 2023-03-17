import subprocess
import sys


def main():
    cp = subprocess.run([sys.executable, "fbuilder", "eforth/eforth_system.fvs", "-o", "eforth/eforth_system.bin", "-fbin", "--sym"], capture_output=True)
    if cp.returncode!=0:
        print(f"Binary generation failed with return code {cp.returncode}")
        print(cp.stdout)
        print(cp.stderr)
        return
    cp = subprocess.run([sys.executable, "fbuilder", "eforth/eforth_system.fvs", "-o", "eforth/eforth_system.S", "-fdisassembly"], capture_output=True)
    if cp.returncode!=0:
        print(f"Disassembly generation failed with return code {cp.returncode}")
        print(cp.stdout)
        print(cp.stderr)
        return


if __name__=="__main__":
    main()
