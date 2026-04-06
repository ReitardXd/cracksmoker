# cracksmoker

a python GUI frontend for hashcat. point it at a hash, pick your attack mode and flags, hit run — it builds the hashcat command and streams the output live.

no cracking logic in python. hashcat does the actual work.

---

## what it does

- auto-detects hash type from the hash you paste (MD5, SHA-1/224/256/512, NTLM, bcrypt, WPA, sha512crypt, sha256crypt, MD5 APR) — picking from the dropdown manually locks it and disables auto-detect for the session
- attack modes: dictionary, combination, brute-force/mask, hybrid
- mask builder — click tokens (`?l ?u ?d ?s ?a`) to build brute-force patterns
- min/max length with `--increment` flags for brute mode
- second wordlist field for combination mode
- rules file, output file, workload profile, extra flags
- live command preview that updates as you change settings
- streams hashcat stdout directly into the log window, colour-coded by event type

---

## requirements

- Python 3.8+
- hashcat (setup.py handles this)
- tkinter (usually bundled with Python, setup.py will try to fix it if not)

---

## install & run

clone the repo and run the setup script — it detects your OS, installs hashcat if needed, then launches the GUI:

```bash
git clone https://github.com/ReitardXd/cracksmoker
cd cracksmoker
python setup.py
```

or if you already have hashcat installed, just run the GUI directly:

```bash
python cracksmoker.py
```

---

## supported platforms

| OS | install method |
|---|---|
| Ubuntu / Debian / Kali | `apt-get install hashcat` |
| Fedora / RHEL | `dnf install hashcat` |
| Arch / Manjaro | `pacman -Sy hashcat` |
| macOS | `brew install hashcat` |
| Windows | `winget install Hashcat.Hashcat` |

---

## usage

1. paste your hash into **TARGET HASH** — the hash type dropdown will auto-detect and update
2. if auto-detect shows the wrong type, pick the correct one manually from **HASH TYPE** (this locks it for the session)
3. pick an **ATTACK MODE**
4. fill in wordlist / mask depending on mode
5. check the command preview looks right
6. hit **RUN**

### attack modes

| mode | use case |
|---|---|
| dictionary | wordlist against a hash |
| combination | combine two wordlists |
| brute-force / mask | exhaustive search with a pattern |
| hybrid dict+mask | wordlist words with mask appended |
| hybrid mask+dict | mask prepended to wordlist words |

### mask tokens

| token | charset |
|---|---|
| `?l` | lowercase a-z |
| `?u` | uppercase A-Z |
| `?d` | digits 0-9 |
| `?s` | special characters |
| `?a` | all printable |

example mask for 8-char lowercase+digit password: `?l?l?l?l?l?l?d?d`

---

## files

```
cracksmoker/
├── cracksmoker.py   # the GUI
├── setup.py         # install hashcat + launch
├── README.md
└── rockyou.txt      # included for testing
```

---

## disclaimer

for educational use and authorized security testing only. don't be an idiot.

---

## contributing

fork it, make a branch, open a PR.
