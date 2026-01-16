
import subprocess
import sys

def run_step(command, step_name):
    print(f"\n🚀 {step_name}")
    result = subprocess.run(command, shell=True)

    if result.returncode != 0:
        print(f"❌ Échec à l'étape : {step_name}")
        sys.exit(1)

if __name__ == "__main__":
    run_step("python src/preprocessing.py", "Preprocessing")
    run_step("python src/train.py", "Training")
    print("\n✅ Pipeline terminé avec succès")