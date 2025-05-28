# Database Setup Guide

This guide will walk you through setting up the PostgreSQL database for the ideation application using Docker.

## Prerequisites

Before running the database setup commands, you need to complete the following steps:

### 1. Install PostgreSQL
Download and install PostgreSQL from the [official website](https://www.postgresql.org/download/) for your operating system.

### 2. Install and Start Docker Desktop
- Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/)
- Install and launch Docker Desktop
- Ensure Docker Desktop is running before proceeding

## Database Container Setup

### 3. Start PostgreSQL Container
Run the following command to create and start a PostgreSQL container:

```bash
docker run --name postgres-ideation ^
    -e POSTGRES_PASSWORD=user_password ^
    -e POSTGRES_DB=ideation_db ^
    -e POSTGRES_USER=postgres ^
    -p 5432:5432 ^
    -d postgres:15
```

**Note:** The `^` character is used for line continuation in Windows Command Prompt. If you're using:
- **PowerShell**: Replace `^` with `` ` `` (backtick)
- **Linux/macOS**: Replace `^` with `\` (backslash)
- **Single line**: Remove `^` and put everything on one line

### 4. Validate Database Connection
Test that the database is running and accessible:

```bash
docker exec -it postgres-ideation psql -U postgres -d ideation_db
```

If successful, you should see the PostgreSQL command prompt. Type `\q` to exit.

## Database Setup Commands

Once your PostgreSQL container is running and validated, execute the following commands in order:

### Create Database Schema
```bash
python scripts/database_setup.py create
```

### Test Database Setup
```bash
python scripts/database_setup.py test
```

### Load Demo Data
```bash
python scripts/database_setup.py demo
```

### View Database Statistics
```bash
python scripts/database_setup.py stats
```

## Troubleshooting

- **Container already exists**: If you get an error about the container name already existing, either remove the existing container with `docker rm postgres-ideation` or use a different name
- **Port already in use**: If port 5432 is already in use, change `-p 5432:5432` to `-p 5433:5432` and update your application configuration accordingly
- **Connection refused**: Ensure Docker Desktop is running and the container is started with `docker ps`

## Next Steps

After successfully completing these steps, your PostgreSQL database should be ready for use with the ideation application.
