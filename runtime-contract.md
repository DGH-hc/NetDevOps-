### 1\.**Purpose of This Document**

This document defines the runtime behavior of the NetDevops Platfrom application 



It is a runtime contract between:

* the application
* Docker images
* Kubernetes
* Helm charts
* CI/CD piplines

&nbsp;Any deployment logic, Helm configuration, or CI workflow must follow the rules defined here.



If behavior is not defined in this document, it must not be assumed.



## 2\.**Container Image Overview**

The NetDevOps Platform is  built as a single Docker image.



The same image is reused to run:



* the API server
* background workers
* database migrations



The behavior of the container is determined only by the command and arguments provided at startup.

The image itself does not change between environments or roles.



#### 3\.**Supported Runtime Modes**

The container supports the following runtime modes.



##### 3.1 API Mode 

**Purpose:**

Server HTTP API requests.



**Behavior:**



* Starts the web application server
* Listens on a fixed network port
* Does not run database migrations
* Exposes health endpoints for Kubernetes



**Guarantees:**



* API startup must not modify database schema
* API must be restartable at any time without data loss



#### 3.2 Worker Mode

**Purpose:**

Process background and asynchronous jobs.



**Behavior:**



* Starts the background worker process
* Connects to Redis or message broker
* Does not expose HTTP endpoints
* Does not run database migrations



**Guarantees:**



* Worker processes are independent of API availability
* Worker restarts must not affect API traffic
* Worker must be horizontally scalable





##### 3.3 Migration Mode

**Purpose:**

Apply database schema migrations.



**Behavior:**



* Runs Alembic migrations to the latest version
* Executes once and exits
* Does not start API or worker processes



**Guarantees:**

* Migrations are idempotent and safe to re-run
* Migrations failures must stop the deployment process
* Migrations are never executed automatically on application startup



#### **4. Environment Variable Contract**

The application requires specific environment variables to operate correctly.



##### 4.1 Required Secrets

The following environment variables are required and must be provided via secure secret storage(Kubernetes Secrets):



* DATABASE\_URL

&nbsp;     PostgresSQL connection string

* SECRET\_KEY

&nbsp;     Application secret key

* REDIS\_URL

&nbsp;    Redis connection string



The application must not start successfully if any required secret is missing.



##### 4.2 Required Configuration(Non-Secret)

The following environments variables are required but are **not secrets:**



* ENVIRONMENT

&nbsp;     Allowed values: dev, staging, production

* LOG\_LEVEL 

&nbsp;     Controls application logging verbosity



These values must be explicitly provided by helm values or environment configuration.



#### 5\.**Health Check Contract**

&nbsp;The application exposes health endpoints used by Kubernetes to manage lifecycle and traffic





##### 5.1 Liveness Endpoint

**Endpoint:**

/health/live



**Purpose:**

Indicates that the application process is running.



**Rules:**



* Must not depend on database, Redis , or external services
* Failure indicates the process is broken and must be restarted 



##### 5.2 Readiness Endpoint

**Endpoint:**

/health/ready



**Purpose:**

Indicates that the application is ready to receive traffic.



**Rules:**



* May check database and Redis connectivity
* Failure removes the pod from service traffic
* Failure must not cause automatic restarts

#### 

#### **6. Startup and Migration Guarantees**

The following rules define safe startup behavior:



* The application **must never**  run database migrations automatically on startup
* Database migrations are executed **only** in Migrations Mode
* API and Worker containers may start before migrations are applied
* If database schema is incompatible, the application must fail readiness check but remain running
* Application restarts must be safe and repeatable



These guarantees enable safe rolling deployments and rollbacks.





##### **7. What This Contract Enables**

By enforcing this runtime contract, the system enables:



* Safe Helm upgrade and rollbacks
* CI-controlled database migrations
* Zero-downtime deployments
* Independent scaling of API and workers
* Predictable behavior across all environments





## **End of Runtime Contract**



