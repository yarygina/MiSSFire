# MiSSFire
MIcroService Security Framework (MiSSFire) provides a standard way to embed security mechanisms into microservices written in Python. It addresses the problem of establishing trust between individual microservices. The framework utilizes Mutual Transport Layer Security (MTLS) for mutual authentication of services and traffic encryption, and JSON Web Tokens (JWT) for principal propagation.

The framework consists of a set of infrastructure services that need to be up and running within a system and a template for a regular functional service. Currently, the framework is bundled with two infrastructure services that expose relevant REST APIs:
1) The CA service is a core part of the self-hosted PKI that enables MTLS between microservices. It generates a self-signed root certificate and signs CSR from other services.
2) The Reverse STS stays behind a user authentication service and generates security tokens in JWT format. A new JWT is generated per user request.

The template for a regular functional service simplifies integration with the infrastructure services by providing all the necessary functionality. Additionally, it forces use of MTLS for all connections and requires presence of JWT for all incoming requests. 

The framework is written in Python v2.7 programming language. OpenSSL v1.0.2 is used for certificate generation and Flask JWT extension for JWT tokens creation. The framework services can be run as separate processes or inside Docker containers (Dockerfiles are provided).

A fictitious microservice-based banking system is used to show how the framework can be utilized. 

To run in Docker:
1) Build the necessary Docker images 
./build.sh -i
2) Copy the required files into a project (in this case the MicroBank project)
./build.sh -c
3) Run the bank model with MiSSFire
MicroBank/services/build.sh -r
