from os import getenv

POSTGRES_DSN = getenv('POSTGRES_DSN',
                      'postgres://velociped:foobar@localhost:5433/velociped')
