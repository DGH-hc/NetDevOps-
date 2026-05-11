Current system uses single-instance database architecture.

While application and worker layers are horizontally scalable and resilient,
database layer remains a single point of failure.

Next iteration will introduce:
- replication
- failover
- connection abstraction layer