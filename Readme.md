# Docker version of TP1
This project create a docker to run the test for TP1 requirements. You may find the related code [here](https://github.com/bauuuu1021/cloud-computing-tp1).

## Before Execution
### Account information
Copy the information from `Account Details` of the aws website, including 
* aws_access_key_id
* aws_secret_access_key
* aws_session_token.

And paste to the corresponding environment variables in `Dockerfile`.
### Login Key
Also copy the login key (*.pem) to the root directory of this project and change the file mode
```
$ chmod 400 <*.pem>
```
and replace every `ec2-keypair` in `Dockerfile` and `final.py` with the name of your login key
## Execution
```
$ ./script.sh
```
