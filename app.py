from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging
import pymongo
logging.basicConfig(filename="scrapper.log" , level=logging.INFO)

app = Flask(__name__)

# by defalt rending web page 
@app.route("/", methods = ['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review" , methods = ['POST' , 'GET'])  # bcz when submit button is called then form action is /review 
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ","")   # content is the input name in text input 
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = uReq(flipkart_url)  # to open the link
            flipkartPage = uClient.read()  # to read the page
            uClient.close()              # to close the link becz we have the content inside of flipkartpage var 
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})   # product box  
            del bigboxes[0:3]
            
            box = bigboxes[0]  # for the first product box  
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']    # finding the product link
            prodRes = requests.get(productLink)      # click the product link 
            prodRes.encoding='utf-8'   #  you are telling the HTTP library to decode any text content in the response using the UTF-8 encoding, which should ensure that the text is displayed correctly.
            prod_html = bs(prodRes.text, "html.parser")  # now we have the text source of product page
            print(prod_html)
            commentboxes = prod_html.find_all('div', {'class': "_16PBlm"})   # reaching to the all comment boxs with help of class name _16PBlm

            filename = searchString + ".csv"  # creating a csv file with file name as search prod name  
            fw = open(filename, "w")          # creating a csv file to store commentbox content heading
            headers = "Product, Customer Name, Rating, Heading, Comment \n"
            fw.write(headers)                 # writing the content of headers
            reviews = []
            for commentbox in commentboxes:    # iterating on all the comment box having class name _16PBlm 
                try:
                    #name.encode(encoding='utf-8')
                    name = commentbox.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text  # reaching to the name of commenter

                except:
                    logging.info("name")

                try:
                    #rating.encode(encoding='utf-8')  
                    rating = commentbox.div.div.div.div.text   # reaching to the ratting of comment

                except:
                    rating = 'No Rating'
                    logging.info("rating")

                try:
                    #commentHead.encode(encoding='utf-8')
                    commentHead = commentbox.div.div.div.p.text   # reaching to the short comment

                except:
                    commentHead = 'No Comment Heading'
                    logging.info(commentHead)
                try:
                    comtag = commentbox.div.div.find_all('div', {'class': ''})  # reaching to the comment
                    #custComment.encode(encoding='utf-8')
                    custComment = comtag[0].div.text
                except Exception as e:
                    logging.info(e)

                mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                          "Comment": custComment}    # we are storing all the data inside of the dic 
                reviews.append(mydict)               # appending the data inside of list reviwes 
            logging.info("log my final result {}".format(reviews))
            
           
            client = pymongo.MongoClient("mongodb+srv://nikhilsinghxlx:Password@cluster0.9kjhcgg.mongodb.net/?retryWrites=true&w=majority")
            db = client['review_scrap']
            review_col = db['review_scrap_data']
            review_col.insert_many(reviews)

            return render_template('result.html', reviews=reviews[0:(len(reviews)-1)])  # renderdring the result on result web page from one to last

        except Exception as e:   # if any exception is there it will not reander result.html and will only display 'something is wrong'
            logging.info(e)
            return 'something is wrong'

    
    else:
        return render_template('index.html')


if __name__=="__main__":
    app.run(host="0.0.0.0")
