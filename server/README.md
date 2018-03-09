This is a rest api framework based on cherrypy routes

configure the file server.conf

run the server
python server.py

optional arguments:
  -h, --help            show this help message and exit
  -c BACKUPCONF, --conf BACKUPCONF
                        backup configuration file
  --version, -v         display version

subcommands:
  valid subcommands

  {run,role,db}         additional help
    run                 start server
    role                role operation
    db                  database operation


start the server on background

python server.py run