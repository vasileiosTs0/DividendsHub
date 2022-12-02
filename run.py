from dividendshub import create_app
from dividendshub.config import basedir

if __name__ == '__main__':
    server = create_app()
    server.run(debug=True)
