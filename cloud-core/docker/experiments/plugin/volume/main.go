// A fake volume driver taken from
//   http://blog.csdn.net/halcyonbaby/article/details/47325177
// with modification for newer docker version (1.12)
//
// Steps:
//  1. go build .
//  2. sudo ./volume
//  3. docker volume create -d fakeVol --name test
//  4. docker run --rm -it -v test:/abc --volume-driver=fakeVol ubuntu bash
//  5. Test it works by touch a file in /abc, and look into /var/lib/fakevol/test
//  6. sudo rm -rf /run/docker/plugins/fakeVol.sock

package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sync"

	dkvolume "github.com/docker/go-plugins-helpers/volume"
)

var (
	root = flag.String("root", "/var/lib/fakevol", "fake volumes root directory")
)

type fakeVolDriver struct {
	root    string
	m       *sync.Mutex
	volumes map[string]string
}

func newFakeVolDriver(root string) fakeVolDriver {
	d := fakeVolDriver{
		root:    root,
		volumes: map[string]string{},
		m:       &sync.Mutex{},
	}
	os.Mkdir(root, 0755)
	return d
}

func (d fakeVolDriver) Create(r dkvolume.Request) dkvolume.Response {
	log.Printf("Creating volume %s\n", r.Name)
	d.m.Lock()
	defer d.m.Unlock()
	volPath := filepath.Join(d.root, r.Name)
	if _, err := os.Stat(volPath); os.IsNotExist(err) {
		os.Mkdir(volPath, 0755)
		d.volumes[r.Name] = volPath
	}
	return dkvolume.Response{}
}

func (d fakeVolDriver) Remove(r dkvolume.Request) dkvolume.Response {
	log.Printf("Removing volume %s\n", r.Name)
	d.m.Lock()
	defer d.m.Unlock()
	if _, err := os.Stat(d.volumes[r.Name]); os.IsNotExist(err) {
		os.Remove(d.volumes[r.Name])
		delete(d.volumes, r.Name)
	}

	return dkvolume.Response{}
}

func (d fakeVolDriver) Get(r dkvolume.Request) dkvolume.Response {
	d.m.Lock()
	defer d.m.Unlock()
	if _, ok := d.volumes[r.Name]; ok {
		return dkvolume.Response{
			Volume: &dkvolume.Volume{
				Name:       r.Name,
				Mountpoint: d.volumes[r.Name],
			},
		}
	} else {
		return dkvolume.Response{
			Err: "Not found",
		}
	}
}

func (d fakeVolDriver) List(r dkvolume.Request) dkvolume.Response {
	d.m.Lock()
	defer d.m.Unlock()
	log.Printf("Listing volume\n")
	response := dkvolume.Response{}
	for name, path := range d.volumes {
		response.Volumes = append(response.Volumes, &dkvolume.Volume{Name: name, Mountpoint: path})
	}
	return response
}

func (d fakeVolDriver) Path(r dkvolume.Request) dkvolume.Response {
	return dkvolume.Response{Mountpoint: d.volumes[r.Name]}
}

func (d fakeVolDriver) Mount(r dkvolume.MountRequest) dkvolume.Response {
	return dkvolume.Response{Mountpoint: d.volumes[r.Name]}
}

func (d fakeVolDriver) Unmount(r dkvolume.UnmountRequest) dkvolume.Response {
	return dkvolume.Response{}
}

func (d fakeVolDriver) Capabilities(r dkvolume.Request) dkvolume.Response {
	return dkvolume.Response{}
}

func main() {
	flag.Parse()

	// 'go-plugins-helpers' will create a socket file under '/run/docker/plugins/fakeVol.sock'.
	d := newFakeVolDriver(*root)
	h := dkvolume.NewHandler(d)
	fmt.Println(h.ServeUnix("root", "fakeVol"))
}
