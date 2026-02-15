
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

    # Ce fichier peut il etre executer en ligne de commande ? sans focrecement le deploiement d'un conteneur ?
    # Oui, il peut être exécuté en ligne de commande tant que les dépendances sont installées et que les chemins d'accès sont corrects. Cependant, il est conçu pour être exécuté dans un environnement de conteneur Docker, comme spécifié dans le Dockerfile et le docker-compose.yml. Si vous souhaitez l'exécuter en dehors d'un conteneur, assurez-vous que toutes les dépendances sont installées et que les chemins d'accès aux fichiers sont corrects.