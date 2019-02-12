// Adding a file directly to index (stage area), without using working tree.
//
// $ go build . && yes | mv go-git ~/code/workspace/bin
// $ mkdir /tmp/sample && cd /tmp/sample
// $ go-git
package main

import (
	"fmt"
	"os"
	"time"

	"gopkg.in/src-d/go-billy.v4/memfs"
	"gopkg.in/src-d/go-billy.v4/osfs"
	"gopkg.in/src-d/go-git.v4"
	. "gopkg.in/src-d/go-git.v4/_examples"
	"gopkg.in/src-d/go-git.v4/plumbing/object"
	fsfs "gopkg.in/src-d/go-git.v4/storage/filesystem"
)

func main() {
	// This is our filesystem in memory.
	mem := memfs.New()

	// Create a new git directory with working tree.
	s := fsfs.NewStorage(osfs.New(".git"), nil)
	r, err := git.Init(s, mem)
	CheckIfError(err)

	// This is our working tree (wraps memfs).
	t, err := r.Worktree()
	CheckIfError(err)

	//
	// Create a new file in memfs, add & commit to git.
	file, err := mem.Create("greeting.txt")
	CheckIfError(err)
	file.Write([]byte("Hello, World in greeting.txt!"))

	_, err = t.Add("greeting.txt")
	CheckIfError(err)

	ch1, err := t.Commit("Add greeting.txt", &git.CommitOptions{
		Author: &object.Signature{
			Name:  "John Doe",
			Email: "john@doe.org",
			When:  time.Now(),
		}})
	CheckIfError(err)
	fmt.Println(ch1)

	//
	// Create a new file in memfs under a folder, add & commit to git.
	err = mem.MkdirAll("dir", os.ModeDir)
	CheckIfError(err)
	file, err = mem.Create("dir/hello.txt")
	file.Write([]byte("Hello, World in hello.txt!"))

	_, err = t.Add("dir/hello.txt")
	CheckIfError(err)

	ch2, err := t.Commit("haha", &git.CommitOptions{
		Author: &object.Signature{
			Name:  "John Doe",
			Email: "john@doe.org",
			When:  time.Now(),
		}})
	CheckIfError(err)
	fmt.Println(ch2)

	// Now we have two commits in our repositories, we find the commit tree and
	// compare the changes.
	co1, err := r.CommitObject(ch1)
	CheckIfError(err)
	to1, err := r.TreeObject(co1.TreeHash)
	CheckIfError(err)

	co2, err := r.CommitObject(ch2)
	CheckIfError(err)
	to2, err := r.TreeObject(co2.TreeHash)
	CheckIfError(err)

	changes, err := to1.Diff(to2)
	CheckIfError(err)

	// We'll see only one change: Added "dir/hello.txt"
	for i, change := range changes {
		fmt.Printf("%v: %+v\n", i, change)
	}
}
