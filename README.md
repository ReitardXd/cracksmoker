# cracksmoker
<img width="643" height="573" alt="image" src="https://github.com/user-attachments/assets/1778cff6-2baa-4634-846c-a74c0277dfa9" />

# Password Cracker Tool

A powerful and easy-to-use password cracking tool built with Python and Tkinter, capable of performing **dictionary attacks** and **brute-force attacks** to crack common password hashes such as **MD5**, **SHA1**, **SHA256**, **bcrypt**, and **sha512**. The tool utilizes **parallel processing** with **multiprocessing** to speed up the cracking process, and provides a **GUI** for convenient interaction.

## Features
- **Supports multiple hash algorithms**: MD5, SHA1, SHA256, bcrypt, sha512.
- **Parallel processing** with **multiprocessing** for faster cracking.
- **Dictionary attack** using a customizable wordlist file.
- **Brute-force attack** with a user-defined character set and password length.
- **GUI interface** built with Tkinter for an intuitive user experience.
- **Real-time progress updates** and logging with color-coded output.

## Prerequisites

- Python 3.x
- Required Python libraries:
  - `hashlib` (built-in)
  - `itertools` (built-in)
  - `tkinter` (built-in)
  - `multiprocessing` (built-in)
  - `passlib` (optional, for bcrypt and other salted hash support)

You can install the required libraries using the following:

```bash
pip install passlib bcrypt tkinter multiprocessing itertools hashlib
```
#Note: If passlib is not installed, the tool will fall back to basic unsalted hashes (MD5, SHA1, SHA256). 

Installation
Clone this repository or download the password_cracker.py file.

```bash
git clone https://github.com/ReitardXd/cracksmoker
```

## Usage
Launch the GUI
Run the script to launch the Tkinter GUI:
```python password_cracker.py```

## GUI Features
Target Hash: Enter the hash that you want to crack. The hash can be in MD5, SHA1, SHA256, bcrypt, or sha512 format.

## Attack Mode:
Dictionary: Cracks the hash using a wordlist (dictionary attack).

Brute-Force: Cracks the hash by generating passwords from a custom character set.

Wordlist: Provide the path to a wordlist file for dictionary attacks.

Charset & Max Length (Brute-Force Mode): Define the character set (e.g., lowercase letters, digits) and the maximum password length for brute-force attacks.

Threads: Adjust the number of threads for parallel processing (default: number of CPU cores).

Progress Bar: Tracks the progress of the attack in real-time.

Log Window: Displays real-time logs, including success or failure messages.

## Attack Flow
Start Attack: Click the "Start Attack" button to begin the attack with the provided hash and attack mode. The attack will run in the background while updating progress.

Stop Attack: Click the "Stop Attack" button to terminate the attack early if necessary.

## Attack Modes
Dictionary Attack:
Select the "Dictionary" attack mode.

Provide the path to a wordlist file.
The tool will attempt to crack the hash by comparing each word in the wordlist to the target hash.

Brute-Force Attack:
Select the "Brute-Force" attack mode.

Define the charset (e.g., lowercase letters, digits, symbols) and max password length.
The tool will attempt to crack the hash by generating all possible passwords of varying lengths from the charset.

Example
MD5 Hash Example:
If you have a hash 482c811da5d5b4bc6d497ffa98491e38, you can try cracking it using a wordlist file.

SHA256 Hash Example:
Hash 5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8 can be cracked using either a wordlist or brute-force.

## Notes
Ethical Use: This tool is intended for educational purposes or use in authorized security audits only. Unauthorized use is illegal(dont be a dumbass keep stuff ethical ;)).

Performance: The speed of the cracking process is dependent on the hash type, the attack mode, the size of the wordlist, and the number of threads used.

Multi-Core Support: The tool uses multiprocessing to speed up the cracking process, especially during brute-force attacks or large wordlist dictionary attacks.

## Contributing
Feel free to fork this project and submit pull requests with improvements or new features! Contributions are welcome.

Fork the repository.

Create your feature branch (git checkout -b feature-name).

Commit your changes (git commit -am 'Add new feature').

Push to the branch (git push origin feature-name).

Open a pull request.

License
This project is licensed under the MIT License – see the LICENSE file for details.

## Disclaimer
This tool is meant for educational and ethical use only. Use it responsibly and only on systems you own or have explicit permission to test.

Happy Cracking!
