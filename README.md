# Literature Mutations Network Builder

## Description

An ideation of generating a network of literature and applying graph clustering algorithms to derive genres/subgenres (maybe also determine when said genres formed?)

## Credit Where Credit is Due

Goodreads scraper forked from: https://github.com/javierlopeza/goodreads-scraper

My fork: https://github.com/2016judea/goodreads-scraper

![alt text](https://github.com/2016judea/literature-mutations/blob/master/example-output.PNG)

### **Step 1: Select shelves**

Go to https://www.goodreads.com/shelf and select the shelves you want to scrape from.

This is how `shelves.txt` would look like:

```
fantasy
adventure
thriller
```

### **Step 2: Get your cookies**

To retrieve all pages you want you'll need to log in into Goodreads and get the value of your `_session_id2` cookie. Set the value of the constant COOKIE in `constants.py` with the one you obtained from your browser.

### **Step 3: Run books scraper**

```
python .\books_scaper.py
```

You can set how many pages you want to scrape from each shelf by changing the value of the constant `PAGES_PER_SHELF` to whatever you want.

By the end of this step you will end up with 1 json file per page per shelf inside the `shelves_pages` folder. Something like this:

```
fantasy_1.json
fantasy_2.json
fantasy_3.json
adventure_1.json
adventure_2.json
adventure_3.json
thriller_1.json
thriller_2.json
thriller_3.json
```

### **Step 4: Run shelves merger**

```
python .\shelves_merger.py
```

This script will collect all books, remove duplicates, clean the attributes of the books and clean all reviews.

### **Step 5: Generate Network**

```
python .\generate_network.py
```
