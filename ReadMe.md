This is smart book recommendation system. Where user can get book recommendations based on their interest. Which supports following functionalities
    - User can register and login
    - User can add books to their library
    - User can get book recommendations based on their interest
    - User can list all the books in the library
    - User can add review/rate any book
    - User can get the summary of the book
    - User can see the reviews and rating of any book

** Authentication 
    User needs to register and create username and password.
    User can login using username and password to get the access token
    User need to pass the access token to access the protected endpoints

** Book Recommendation & Summary ( Powered by llama3.2 )
    User can get book recommendations based on their interest
    User can get the summary of the book
    User can see the reviews and rating of any book


                    Technical Specifications
- Python 3.9 
- FastAPI
- uvicorn
- llama3.2 hosted locally or on cloud, update the endpoint in .env file
- Postgresql setup, update the database connection in .env file

                    Project Setup
- Clone the repository
- Create a virtual environment
- Install the dependencies, pip install requirements.txt
- update the endpoints in the .env file
- update the database connection in the .env file
- Run "uvicorn main:app"
- Access the swagger endpoint at http://localhost:8000/docs

    

