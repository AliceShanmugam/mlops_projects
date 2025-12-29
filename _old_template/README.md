## Prefect docker official image

You can see : https://hub.docker.com/r/prefecthq/prefect/tags

Moving from `prefecthq/prefect:3-latest` to `docker pull prefecthq/prefect:3.1.16.dev2-python3.12`. See on https://hub.docker.com/r/prefecthq/prefect/tags.

It is recommended to “pin” a Docker image so that you’re locked into a specific version even if the tag (like “3‑latest”) gets updated later. However, there are a couple of points to consider:

1. Why “Pinning” Is Important

Using a mutable tag like 3-latest means that the underlying image can change over time. This could lead to unexpected behavior if a new version is published that isn’t backwards compatible. Pinning ensures that your deployment always uses the exact image you expect.

2. How to Pin an Image

A. Use a Version Tag:
Instead of using 3-latest, you can specify a specific version (for example, 3.0.0rc14-python3.11). This way, you know exactly what you’re running, and it won’t change unexpectedly.

B. Use an Immutable Digest:
Docker images have an immutable identifier called a digest. When you pull an image by digest (e.g., prefecthq/prefect@sha256:<digest>), you’re referencing a specific snapshot of that image. Even if the tag moves, the digest stays the same.

Steps to Pin Using a Digest:
1. Pull the Image by Tag: `docker pull prefecthq/prefect:3-latest`

(Make sure the tag exists. Note that in some cases, like in a GitHub issue , the 3-latest tag might not be available or could have been changed.)

2. Find the Digest:
After pulling, run: `docker inspect --format='{{index .RepoDigests 0}}' prefecthq/prefect:3-latest`

This command returns something like `prefecthq/prefect@sha256:abcdef123456....`

3. Deploy Using the Digest:
Use this digest reference in your deployment commands. For example: `docker pull prefecthq/prefect@sha256:abcdef123456...`

This guarantees that the same image is used every time, regardless of changes to the tag.

3. Special Consideration for Prefect Images

There’s been some discussion on GitHub regarding the 3-latest tag for Prefect images. One issue even reported that deploying with prefecthq/prefect:3-latest resulted in errors because the tag wasn’t found ([ ￼](https://github.com/PrefectHQ/prefect/issues/14384)). In this case, it might be a good idea to either:
	•	Use a version-specific tag that is known to exist.
	•	Or, if you prefer using the “latest” style, first check the digest on Docker Hub and then pin it using the digest.

Example in Simple Steps :

1. Decide on the Image:
Instead of prefecthq/prefect:3-latest, check Docker Hub for Prefect to see available tags.

2. Pin Using a Specific Tag or Digest:
For a specific tag: `docker pull prefecthq/prefect:3.0.0rc14-python3.11` (tested but did worked in my case). That's why I decided to go for the digest.

Or, for a digest: `docker pull prefecthq/prefect@sha256:abcdef123456...`


3. Use in Your Deployment:
Replace the image reference in your deployment configuration with the one you’ve pinned.


mlflow:
    build:
      context: .
      target: development
    command: mlflow server --host 0.0.0.0 --port 5001

# Create deployment

```sh
make deploy
make run
```