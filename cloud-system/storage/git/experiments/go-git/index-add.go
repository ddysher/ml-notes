// Adding a file directly to index (stage area), without using working tree.
//
// $ go build index-add.go && yes | mv index-add ~/code/workspace/bin
// $ mkdir -p /tmp/sample && cd /tmp/sample
// $ index-add
package main

import (
	"gopkg.in/src-d/go-billy.v4/osfs"
	"gopkg.in/src-d/go-git.v4"
	. "gopkg.in/src-d/go-git.v4/_examples"
	"gopkg.in/src-d/go-git.v4/plumbing"
	fsfs "gopkg.in/src-d/go-git.v4/storage/filesystem"
)

func main() {
	// Create a new git directory.
	s := fsfs.NewStorage(osfs.New(".git"), nil)
	r, err := git.Init(s, nil)
	CheckIfError(err)

	// Data to add object
	content := []byte("Hello, World in greeting.txt!")
	path := "directory/greeting.txt"

	// Find index from Storer, here we are using filesystem.
	idx, err := r.Storer.Index()
	CheckIfError(err)

	// Get an object, write data into the object, then save to object storage.
	obj := r.Storer.NewEncodedObject()
	obj.SetType(plumbing.BlobObject)
	obj.SetSize(int64(len(content)))

	// The implementation of "obj.Writer.Write()" is MemoryObject, which
	// makes a copy of the object.
	writer, err := obj.Writer()
	CheckIfError(err)
	_, err = writer.Write(content)
	CheckIfError(err)
	writer.Close()

	// Here we again copy the object from "obj" to underline storage. Once
	// saved, it is officially considered part of git database.
	// ** Improvement Needed to avoid Double Copy**
	h, err := r.Storer.SetEncodedObject(obj)
	CheckIfError(err)

	// Add a new entry (we can use "idx.Entry(path)" to check if path exists).
	e := idx.Add(path)
	e.Hash = h

	// Set index, which will be translated to tree object once we commit.
	r.Storer.SetIndex(idx)
}
