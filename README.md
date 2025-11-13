# OpenGraph Deception Utility

For graph operations, both `--in` and `--out` are **required** and are the first two args passed.

**Exception:** `register-icon` and `merge` do **not** use `--in/--out`.

---

## Basic Examples

Using the base minimum OpenGraph implementation, this example adds a deception node and edge. The example data can be found under the examples folder. To get our icons to show up as Font Awesome icons and not "?" marks, we can use the following command to load the icons:
```
python deceptionClone.py register-icon --url http://127.0.0.1:8080 --token <TOKEN> --type Person --icon user --color #FFD43B
python deceptionClone.py register-icon --url http://127.0.0.1:8080 --token <TOKEN> --type Asset --icon money-bills --color #a0c615
```

Using the example data, we can use the sample query to see our graph:

```
MATCH p = (:Person) - [:Knows] - (:Person) - [Has] - (:Asset)
RETURN p
```

<img width="590" height="300" alt="image" src="https://github.com/user-attachments/assets/93bdd51a-652c-4608-a93c-5e89602ccb7f" />


Now we want to bring some deception into the mix. In this example, let's say that Alice's cash is the deception; we just want to know if Bob is trying to use Alice for her Cash. To do this, we can use deceptionClone to convert the existing Cash node to a deception node.
```
python deceptionClone.py --in example_data.json --out deception_example_data_1.json decept-node --id 567 --name cash --deception-kind Deception --description "fake data to catch the real bad guys"
```
To load our deception Icon, we can run the following:
```
python deceptionClone.py register-icon --url http://127.0.0.1:8080 --token <TOKEN> --type Deception --icon circle-radiation
```

Now the Cash node is labeled as deception. 

<img width="602" height="352" alt="image" src="https://github.com/user-attachments/assets/19684be2-cfef-4c65-a655-2b86221ed506" />

Okay, but what if we wanted to keep the existing Cash asset as legitimate, maybe Alice has a sick zipline and she's worried Bob only wants to know her for the zipline. We can keep the existing paths and add a separate edge/node easily.

```
python deceptionClone.py --in example_data.json --out deception_example_data_2.json attach-deception --id 234 --name Zipline --description "feels like Bob is just here for the zipline"
```

A basic query to show the newly added Zipline asset.

```
MATCH p = (:Person) - [:Knows] - (:Person) - [] -> ()
RETURN p
```

<img width="823" height="390" alt="image" src="https://github.com/user-attachments/assets/692a9a4e-b521-4d83-8d0d-e767cac86fda" />


Another noteworthy utility is merging OpenGraph collections and correlating known overlapping objects from each graph. In the following example, we use two sample deception graphs and merge them into one OpenGraph. Additionally, we correlate a node in each graph which we know represents the same object. This bridges the the two technologies and allows us to pathfind between collections.


## Merging Graphs

```
python deceptionClone.py merge-graphs --graph1 ./examples/gluing/github_graph.json --graph2 ./examples/gluing/ansible_graph.json --correlate R_kgDOM3LdJg::DECEPTION,randy-user-0001
```

Now that the randy user has been correlated to a deception node, we can use a cypher to find a path from GitHub to Ansible.

```
MATCH p = shortestPath((:GHUser) - [*1..] ->(:ATJobTemplate)) RETURN p
```

<img width="979" height="454" alt="image" src="https://github.com/user-attachments/assets/ba4e280a-6b97-4669-82fb-17a247368a2b" />


---

## Commands
**Usage**

```
usage: deceptionClone.py [-h] [--in IN_PATH] [--out OUT_PATH] [--pretty] {clone-node,clone-edge,decept-node,decept-edge,attach-deception,register-icon,merge-graphs} ...

OpenGraph deception utility for manipulating nodes, edges, and graphs.

positional arguments:
  {clone-node,clone-edge,decept-node,decept-edge,attach-deception,register-icon,merge-graphs}
    clone-node          Clone a node; add --annotate for Deception fields + kind.
    clone-edge          Clone an edge; add --annotate to decorate the clone.
    decept-node         Mark an existing node as deception (no new nodes).
    decept-edge         Mark an existing edge as deception (no new edges).
    attach-deception    Create a child deception node and connect via HasDeception.
    register-icon       Register a custom icon type in BloodHound.
    merge-graphs        Merge two OpenGraph JSON graphs into a third.

options:
  -h, --help            show this help message and exit
  --in IN_PATH          Input OpenGraph JSON (not needed for register-icon)
  --out OUT_PATH        Output OpenGraph JSON (not needed for register-icon)
  --pretty              Pretty-print JSON output
```
