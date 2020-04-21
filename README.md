# Cloud-Computing
## Project Decription
The application provides a persistent database of UK-based green energy providers, detailing the percentage of green energy and gas supplied by each company and hosted in Cassandra. The database can be accessed via its RESTful API, using the curl commands given below. The application also pulls information from the external Carbon Intensity API and displays dynamic carbon intensity data for the current half hour in the QMUL region. 
The application is hosted on an AWS t2.medium instance, containerized by Cassandra Docker.
### Installation
```
Sudo apt update
Sudo apt install python3-pip
pip3 install Flask
Sudo apt install docker.io
Sudo snap install microk8s  --classic
Pip3 install pyopenssl
```
### Cassandra database
The application was built by pulling the latest Cassandra Docker Image and running an instance ‘cassandra-test’ within docker via port 9042 (CQL native transport port). 
```
sudo docker pull cassandra:latest
sudo docker run --name cassandra-test -p 9042:9042 -d cassandra:latest
```
The CSV file greenenergy.csv was downloaded from the Git repository and the raw information copied into the home directory of the Cassandra container. 
```
wget -O greenenergy.csv https://raw.githubusercontent.com/RachelButcher/Cloud-Computing/master/greenenergy.csv?token=AO2DO3UPHYYBLU3LHFZD37K6TXN3C
sudo docker cp greenenergy.csv cassandra-test:/home/greenenergy.csv
```
A Cassandra terminal was opened within the ‘cassandra-test’ container, to allow interaction with Cassandra via its native command line shell client (cqlsh). 
```
sudo docker exec -it cassandra-test cqlsh
```
Inside the Cassandra terminal a keyspace was created with basic SimpleStrategy replication and a replication factor of 1. 
```
CREATE KEYSPACE energy WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor' : 1};
CREATE TABLE energy.providers (energyprovider text PRIMARY KEY, greenelectricity int, greengas int);
```
Copy the data from the csv file into the Cassandra database
```
COPY energy.providers(energyprovider,greenelectricity,greengas);
FROM '/home/greenenergy.csv'
WITH DELIMITER=',' AND HEADER=TRUE;
```
Using the Git hosted Dockerfile, requirements.txt and app.py a new image was built and run as a service, exposing the deployment to get an external IP.
```
Sudo docker build . --tag=cassandrarest:v1
Sudo docker run -p 80:80 cassandrarest:v1
```
### REST request and response
The persistent information in the Cassandra database is available for update via the following curl commands from a separate terminal, where the IPv4 Public DNS must match that of the EC2 instance. The database is located at the /energy path.

**GET request: retrieves the full Cassandra database to the terminal**
```
curl -v ec2-54-209-32-201.compute-1.amazonaws.com:80/energy
```
**POST request: adds new energy provider ‘Test’ to the database and sets the value for green electricity (100) and green gas (10). Returns 201 CREATED response code if successful, confirming a new tuple has been created.**
```
curl -i -H "Content-Type: application/json" -X POST -d '{"energyprovider":"Test","greenelectricity":100,"greengas":10}' http://ec2-54-172-10-18.compute-1.amazonaws.com:80/energy
```
**DELETE request: deletes all information associated with the energy provider ‘Test’. Returns 200 OK response code if tuple successfully deleted.**
```
curl -i -H "Content-Type: application/json" -X DELETE -d '{"energyprovider":"Test"}' http://ec2-54-172-10-18.compute-1.amazonaws.com:80/energy
```
**PUT request: updates the column information for the energy provider ‘Test’. Returns 200 OK response code if tuple successfully updated.**
```
curl -i -H "Content-Type: application/json" -X PUT -d '{"energyprovider":"Test","greenelectricity":40,"greengas":6}' http://ec2-54-172-10-18.compute-1.amazonaws.com:80/energy
```
### External Carbon Intensity API 
Information from the external API is accessed through the path /energy/emissions. The external function of the app.py file specifies the outward postcode E1, to retrieve only regional data, in line with the API documentation.

### Kubernetes Load Balancing
Installed microk8s (see installation) and started the cassandra:latest container. 
```
Sudo docker start be0eb285502e
```
The local Docker daemon is not part of the MicroK8s Kubernetes cluster and therefore the image had to be exported from daemon and injected into the Microk8s image cache (tutorial in references). This circumvented previous ‘ErrImagePull’ error messages. The application was deployed and the load balancer service exposed externally, listening at port 80. 
```
Sudo microk8s.kubectl create deployment hello-web --image=docker.io/library/cassandrarest:v1
Sudo microk8s.kubectl expose deployment hello-web --type=LoadBalancer --port=80 --name=my-service
```
The application can be scaled using the following command, where n is the number of replicas. 
```
Sudo microk8s.kubectl scale deployment hello-web --replicas=n
```
*Unfinished feature*

When displaying information about my-service, the external IP address was continually hanging in ‘pending’. It may be assumed that the service did not fully expose externally and therefore the success of deploying Kubernetes Load Balancing could not be tested by accessing the application via ‘curl http://<external-ip>:<port>’.
  
### HTTPS/SSL Authentication
Set the security groups in AWS to allow HTTPS traffic. Installed pyOpenSLL python package (see installation) and generated a 4096-bit RSA private key and self-signed certificate, ensuring copies of the .pem files were generated in the application project directory. 
```
Openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```
Edited the app.run() function of the flask app.py to contain ‘ssl_context=(‘cert.pem’, ‘key.pem’)
New line reads:
```
App.run(hosts=’0.0.0.0’, port=80, ssl_context=(‘cert.pem’, ‘key.pem’))
```
*Unfinished feature*

Although this addition allowed the application to be accessed via direct https URL, the browser displays a warning regarding the security of the self-signed certificate. The feature has also not been implemented as the curl requests are no longer able to complete, due to curl being unable to verify the legitimacy of the server and therefore not establish a secure connection. 
Attempted to obtain a CA-signed certificate through Let’s Encrypt but was unable to create a domain name to link to the instance’s IP address and was unable to access Amazon Route 53 through AWS Educate. 

### References
[Carbon Intensity API](https://api.carbonintensity.org.uk/)

[Renewable energy provider statistics](https://www.t3.com/features/best-green-energy-supplier)

[Using local Microk8s images](https://microk8s.io/docs/registry-images)

[Serving application over HTTPS](https://stackoverflow.com/questions/29458548/can-you-add-https-functionality-to-a-python-flask-web-server)
