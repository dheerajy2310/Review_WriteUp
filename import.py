import os,csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(
    "postgres://urnadomzdyokuz:34e8498fdeb24dcff2e22f69c5ca42eb6b0b3cff84023641c1f2703c9d4e3c35@ec2-35-169-254-43.compute-1.amazonaws.com:5432/d8n4jqnbfih3nb")
db = scoped_session(sessionmaker(bind=engine))

def main():
    x=open("books.csv")
    reader=csv.reader(x)
    for isbn,title,author,year in reader:
        if isbn!="isbn":
            db.execute("insert into books(isbn,title,author,year) values(:isbn,:title,:author,:year)",{"isbn":isbn,"title":title,"author":author,"year":year})
    db.commit()

if __name__ == "__main__":
    main()