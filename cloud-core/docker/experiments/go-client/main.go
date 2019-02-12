package main

import (
	"fmt"
	"os"
	"strings"

	docker "github.com/fsouza/go-dockerclient"
)

func main() {
	endpoint := "unix:///var/run/docker.sock"
	client, _ := docker.NewClient(endpoint)
	var err error
	var opts docker.PullImageOptions

	if false {
		images, _ := client.ListImages(docker.ListImagesOptions{All: true})
		for _, image := range images {
			fmt.Println("ID:", image.ID)
			fmt.Println("RepoTags:", image.RepoTags)
			fmt.Println("Created: ", image.Created)
			fmt.Println("Size: ", image.Size)
			fmt.Println("VirtualSize: ", image.VirtualSize)
		}
	}

	// "All" option will list all (running + stopped) containers.
	if false {
		containers, _ := client.ListContainers(docker.ListContainersOptions{All: true})
		for _, container := range containers {
			if false {
				fmt.Println("ID:", container.ID)
			}
		}
	}

	if false {
		opts := docker.PullImageOptions{Repository: "python:2.7", OutputStream: os.Stdout}
		err := client.PullImage(opts, docker.AuthConfiguration{})
		if err != nil {
			fmt.Println("Error pulling images:", err)
		} else {
			fmt.Println("Image pulled")
		}
	}

	// Equivalent with the above option.
	if false {
		opts = docker.PullImageOptions{Repository: "python", Tag: "2.7", OutputStream: os.Stdout}
		err = client.PullImage(opts, docker.AuthConfiguration{})
		if err != nil {
			fmt.Println("Error pulling images:", err)
		} else {
			fmt.Println("Image pulled")
		}
	}

	if false {
		opts = docker.PullImageOptions{Repository: "python", Tag: "2.7", OutputStream: os.Stdout}
		err = client.PullImage(opts, docker.AuthConfiguration{})
		if err != nil {
			fmt.Println("Error pulling images:", err)
		} else {
			fmt.Println("Image pulled")
		}
	}

	// Pull from another registry.
	if false {
		opts = docker.PullImageOptions{Repository: "gcr.io/google_containers/pause", OutputStream: os.Stdout}
		err = client.PullImage(opts, docker.AuthConfiguration{})
		if err != nil {
			fmt.Println("Error pulling images:", err)
		} else {
			fmt.Println("Image pulled")
		}
	}

	// 'ddysher/musicjsns' is a private repo, we must provide credential.  Failing to provide
	// credential (wrong credential or no credential) will results in 'image not found' error.
	if false {
		opts = docker.PullImageOptions{Repository: "ddysher/musicjsns", OutputStream: os.Stdout}
		auths, _ := docker.NewAuthConfigurationsFromDockerCfg()
		err = client.PullImage(opts, auths.Configs["https://index.docker.io/v1/"])
		if err != nil {
			fmt.Println("Error pulling images:", err)
		} else {
			fmt.Println("Image pulled")
		}
	}

	if true {
		a, b := ParseRepositoryTag("index.caicloud.io/hello-world:latest")
		fmt.Println(a)
		fmt.Println(b)
	}
}

func ParseRepositoryTag(repos string) (string, string) {
	n := strings.Index(repos, "@")
	if n >= 0 {
		parts := strings.Split(repos, "@")
		return parts[0], parts[1]
	}
	n = strings.LastIndex(repos, ":")
	if n < 0 {
		return repos, ""
	}
	if tag := repos[n+1:]; !strings.Contains(tag, "/") {
		return repos[:n], tag
	}
	return repos, ""
}
