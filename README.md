# Secure Multi-Party Homomorphic Encryption for Biometric Matching

## Overview
This project implements **secure biometric template matching** using **Multiparty Homomorphic Encryption (MHE)** with the **BFV scheme** from TenSEAL. The goal is to enable privacy-preserving fingerprint verification while ensuring no single party has access to the full biometric template.

The system follows an **Additive Secret Sharing + Homomorphic Encryption** approach across two independent servers to compute similarity scores securely.

## Features
- **Homomorphic Encryption (BFV Scheme)** using **TenSEAL**
- **Two-party computation** for biometric template matching
- **Manhattan Distance Computation** over encrypted data
- **Euclidean Distance Computation** over encrypted data
- **Secure Secret Sharing** for biometric templates
- **Client-Server Communication** using **Sockets**

## System Architecture
1. **Database_splitter**
   - Takes the FingerPrintDatabase from IrisFingerPrintDatabases and splits every entry into two shares
   - One random and one template minus the random sequence
   - Stores the one share in **server1_database** and one in **server2_database**


2. **Client**
   - Loads the biometric probe (query fingerprint)
   - Splits it into two secret shares  (one random, and one template minus random)
   - Encrypts each share with **BFV**
   - Sends encrypted shares to **Server 1** and **Server 2** together with ID (4-digit number)


3. **Server 1 & Server 2**
   - Load their respective stored biometric templates  
   - Compute the difference between the encrypted templates and encrypted probe  
   - Send the encrypted difference back to the client


4. **Client**
   - Reconstructs the encrypted difference  
   - Computes **Homomorphic Manhattan Distance**
   - Decrypts the result and determines **matching thresholds**
   - (These operations would in practice be done by either one of the servers or a third server, but for testing I just did it in this file. )


5. **Split_db_test & additive_secret_sharing**
   - Just for testing the logic and debugging
   
## Setup & Installation
### Prerequisites
- Python 3.9+
- Install required dependencies:
  ```sh
  pip install tenseal numpy
  


## Run

- to run the configuration, run first the two servers, then the client
- Install required dependencies:
  ```sh
  python server1.py
  python server2.py
  python client.py
  

to change the probe and template, change line 56 and 58 in **client.py**
  
