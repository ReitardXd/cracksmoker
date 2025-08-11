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
pip install passlib bcrypt
