# Literature Mutations Network Builder

**DESCRIPTION**

Generating a network of literature and applying graph clustering algorithms to derive genres/subgenres (maybe also determine when said genres formed?)

**ABSTRACT**

English Literature’s genres have come to serve as its key mode of classification. However, the rate at which genres and subgenres are formed throughout English Literature’s history is hardly definitive and primarily determined by experts in the field of English Literature in a non-analytical fashion - that is, purely on the basis of opinion. Quantitative research to date as to English Literature’s genres has primarily focused on the semantics of literature’s text and discerning its attributes. Notably, quantitative formalism at Stanford’s Literary Lab has shown that natural language processing techniques are capable of recognizing novelistic genres by the semantics of literature’s text [8]. Yet, this method, as well as any other quantitative method as far as published research to date is concerned, has yet to be applied to analyzing the formation of subgenres and genres as a whole over English Literature’s history and even more specifically to the rate at which new genres and mutated subgenres form. Being that literature’s genres are hardly static, and contain multitudes of genres and subgenres spanning poetry, drama, non-fiction, and fiction (just to name a few), this research will be focused solely in the realm of fiction. Thereby, I propose to study English Literature’s genre mutation rate, specifically within the bounds of fiction, throughout history to form an expected value of this rate for the future.

**CCS CONCEPTS**

Applied computing → Arts and humanities → Fine Arts

**KEYWORDS**

Social Networks, English Literature, Genre Mutation

**1 INTRODUCTION AND BACKGROUND**

Up until very recently (relatively speaking), all research in the realm of English Literature was done by non-analytical means. The Western canon, classification of novels themselves into distinctive genres and subgenres, and even the novels taught in schools fell to the opinionated analysis of the intellectual influential throughout the ages. But for the first time in history, this has begun to change. With the increasing technical aptitude of today’s researchers (even those not specifically doing research in technical fields) we have seen a rise in quantitative techniques being applied to fields of historically non-analytical context (more commonly known as the emerging “Digital Humanities” field). This has only been further heightened in the areas of machine learning and specifically natural language processing with the increased availability of open source libraries that allow said analysis to be done with relative ease. And while the foundations of English Literature can hardly be updated to be formed purely on the basis of quantitative analysis (and nor should they be) there is still room for quantitative analysis to reveal traits of the field that are veiled to purely qualitative methods.

For starters, how would one go about outlining the mutation of fiction’s genres using only qualitative means? It would most likely begin by reading hundreds of books with subsets that represent a sparse variation of each genre and subgenre. From here, you’d look for semantic indicators within the works of literature themselves, note publication dates, and research the political context at the time of publication to form a timeline as to how such genres formed. The obvious flaw in this method is the inherent dispositions we have as humans. These range drastically and in varying degrees of proportion, but ultimately inhibit our ability to say decisively that a novel should or shouldn’t belong in a given genre. However, in the ideal case, quantitative formalism provides the means to forgo such dispositions and derive genres by their semantic form, content, and style - much to the utopic state of the term. And perhaps the most important aspect of this quantitative method is that it allows a means of examining thousands of texts on a year-by-year basis per a work’s publication year to build a complete picture of genre inception and mutation.

While quantitative formalism provides a means of analyzing texts by means of minimal disposition, it is limited in viability by the availability of necessary data. That said, quantitative methods are still available for this research problem and ultimately provide the same ability to discern meaning in the field of English Literature where little to none currently exist.

**2 DATA**

This research is dependent upon acquiring data surrounding literature published on a year-by-year basis for a given period of time. While it would be ideal to capture every work of fiction published in digital form spanning as far back as the written word has been present, this is simply not feasible. Instead, there are a couple ways to build a limited subset of data that would serve as the basis of this research.

(1) In the United States, novels published before January 1, 1925 have lost their copyright protection and are in the public domain. As such, there are a number of corpora across the internet that maintain tens of thousands of texts spanning back hundreds of years. Notably, there is Project Gutenberg and Google Books. While neither of these would provide every work of English Literature published for a given time period (say 1825 to 1925 for example), it would provide a core set of English Literature’s most prominent texts which are generally the type of works that come to define genres as they are currently defined.

(2) While not as ideal as using quantitative formalism due to modern literary genre constructs, another alternative dataset would be to use the Goodreads API [4] or simply web scraping the Goodreads genre shelves [5] to build a core dataset of novels, their published date, and their modernly defined genres based upon the shelves users list them as. The upside to this dataset is that it is not as sparse as the corpora outlined in dataset (1) (more titles available per year that is) and also provides data from 1925 to present day, which helps tremendously with forming an expected value for genre mutation as it stands today. Additionally, as shown by Galton [3], it is perhaps more credible than one would initially think to leave the construction of genres to the everyday reader. The downside to this dataset, when using a novel's “Popular Shelves” specifically and not Goodreads’ assigned genres, is that this data would have to be cleansed prior to feeding it into the model. This is because there are some user shelves such as “Want to Read” that don’t provide genre qualities like that of a “1900s Westerns” shelf.

Due to the limited nature of the dataset defined in alternative (1), the basis of this project will be founded upon the data built via option (2). That said, alternative (1) and its use case will be discussed as part of this project proposal since it is the ideal dataset for this type of research and is also worth discussing contrary to dataset (2) in order to more clearly define the basis upon which the research’s network will be formulated and analyzed.

**3 BUILDING THE NETWORK**

Building the network based upon the acquired data becomes the next logical step of this research. The network is modeled as a graph _G = (V, E)_ where the nodes in _V_ represent novels and the edges in \_E \_represent a relationship between two given novels. Seeing that the relationship between two given novels will represent how similar they are, the edges will be undirected.

The graph itself will be iteratively populated on a year-by-year basis such that a single new node will be added to _V_ for each novel published in a given year and edges will be added to _E \_for each valid relationship between the new node 𝑣 ∈ \_V_ and some other node* u ∈ V* where the validity of the relationship, or rather the similarity measure, is determined by a threshold function _t(u, v)_ → {0, 1}.

Of course, the natural question becomes how this threshold function is defined. Ultimately, the threshold function needs to discern novels that are similar - specifically in terms of the genre(s) each is classified as. Using the Goodreads dataset, we have available each novel’s shelves. Goodreads shelves are the way users classify novels when saving them to their Goodreads library for personal reference. Examples range from fiction’s widely accepted genres such as mystery, romance, and fantasy to more exclusive subgenres like urban fantasy, gothic romance, and thrillers. From these shelves, we build a factor. For example, say there are 1000 users who have a novel on their “Mystery” shelf and 3000 users have the same novel on their “Thriller” shelf. Then the genre factor for this novel would be {Mystery: .25, Thriller: .75}. From this factor, we can determine a level of similarity that will serve as the basis for the threshold function which decides whether an edge _e ∈ E_ is present between _u,𝑣 ∈ V_.

**4 GENRE CLUSTERING TECHNIQUES**

As the data is iterated on a year-by-year publication date basis, the network will continue to grow and clusters will begin to develop; the largest clusters being fiction’s genres and sub-clusters being the subgenres of a given genre. From this, arises perhaps the most pivotal consideration as to this research proposal: What properties define a cluster and sub-cluster in this network such that the network accurately represents genres and subgenres within the realm of English Literature’s works of fiction?

One consideration would be tuning the threshold function _t(u, v)_ to generate a graph that has a number of clusters corresponding to the number of widely accepted genres of fiction using partitional clustering methods [1]. However, classifying definitive fiction genres is an area of intense debate and minimal constructs in the field of English Literature. Additionally, using a partitional clustering method organizes data into non-overlapping groups which seems like a generalization for a set of data that is excessively diverse and inherently spanning multiple genres and subgenres. That said, it does provide a clear method of forming the desired number of genre clusters and tuning the threshold function as needed to meet this criteria.

Alternatively, using a hierarchical clustering method [1] to classify data seems like a more natural clustering algorithm being that genres and subgenres are intrinsically related. Using this method results in the further question of whether a top-down (divisive) or bottom-up (agglomerative) approach should be used, which leads to the consideration of whether genres are inherently formed by their subsequent subgenres or whether subgenres form as an effectuation of overarching genres [6]? Maybe this could be answered by watching the graph as a whole formed on a year-by-year publication basis?

**5 DETERMINING EXPECTED VALUE**

From the formation of a network of fictional novels based upon genre similarity, we can ultimately discern at what rate clusters fabricate and subgenres mutate. This rate, compared on a year-by-year publication basis will provide insights as to the expected number of genre mutations within the realm of English Literature’s fictional genus in the years to come.

Obvious questions that arise from this supposition revolve around how this expected valuation is determined. Is it simply a linear regression that forms this expected value? Or due to the increasing variability of subgenres should this be an application of the power law? Determination of an appropriate expected value function would ultimately be heavily based upon the properties of the resulting data itself.

**6 ALTERNATIVE METHODS**

As noted prior, an alternative dataset for this research would be using digital copies of novels and analyzing them using quantitative formalism techniques to discern genre from the ground up. That is, with as minimal human disposition as possible. This dataset would instead utilize Language Action Types (LATs) to quantify the type, content, and style of novels. LATs, as used by Jonathan Hope and Michael Witmore [7] via the text tagging device Docuscope [2], are a collection of functional linguistic categories that classify more than 200 million possible strings of English. Thereby, LATs would replace Goodreads shelves when classifying a novel’s inherent qualities.

Whether using LATs or Goodreads shelves, once the underlying novels have their genre properties exposed quantitatively, the process of building the network, performing cluster analysis, and evaluating expected values for genre mutation would be nearly identical (with the exception of the threshold function since that would be tuned specific to the data being utilized).

**7 DISCUSSION**

While there are uncertainties surrounding the acquisition and preparation of the data required for this research, there is a straightforwardness of method and extensiveness of impact that make intriguing results a strong possibility. Moreso, for hundreds (if not thousands) of years, English Literature has perhaps been the most kaleidoscopic examination of the human condition we’ve come to acquaint ourselves with. Therefore, it seems like divulging its inherent genre patterns is a worthwhile and edifying venture.

**REFERENCES**

[1] A.P. Reynolds, G. Richards, B.De La Iglesia, and V.J. Rayward-Smith. 2006. Clustering Rules: A Comparison of Partitioning and Hierarchical Clustering Algorithms. _Journal of Mathematical Modelling and Algorithms_ 5, 4 (2006), 475–504. DOI:http://dx.doi.org/10.1007/s10852-005-9022-1

[2] David S. Kaufer, Suguru Ishizaki, Brian S. Butler, and Jeff Collins. 2013. _The Power of Words: Unveiling the Speaker and Writer's Hidden Craft_, New York, NY: Routledge.

[3] Francis Galton. 1907. Vox Populi. Nature 75, 450–451. (2020). https://doi.org/10.1038/075450a0

[4] Goodreads Inc. 2020. Goodreads API. (2020). https://www.goodreads.com/api

[5] Goodreads Inc ed. 2020. Goodreads Genres. (2020). https://www.goodreads.com/genres/list

[6] John E. Stone, Juan R. Perilla, Keith Cassidy, and Klaus Schluten. 2017. Chapter 11 - GPU-accelerated molecular dynamics clustering analysis with OpenACC Rob Farber, ed. _Parallel Programming with OpenACC_ (2017), 215–240.

[7] Jonathan Hope and Michael Witmore. 2004. The Very Large Textual Object: A Prosthetic Reading of Shakespeare. _Early Modern Literary Studies_ 9, 3 (January 2004), 6–36.

[8] Sarah Allison, Ryan Heuser, Matthew Jockers, Franco Moretti, and Michael Witmore. 2011. Quantitative Formalism: An Experiment. (January 2011). https://litlab.stanford.edu/LiteraryLabPamphlet1.pdf

**IMPLEMENTATION**

**_Credit Where Credit is Due_**

Goodreads scraper forked from: https://github.com/javierlopeza/goodreads-scraper

My fork: https://github.com/2016judea/goodreads-scraper

**_Step 1: Select shelves_**

Go to https://www.goodreads.com/shelf and select the shelves you want to scrape from.

This is how `shelves.txt` would look like:

```
fantasy
adventure
thriller
```

**_Step 2: Get your cookies_**

To retrieve all pages you want you'll need to log in into Goodreads and get the value of your `_session_id2` cookie. Set the value of the constant COOKIE in `constants.py` with the one you obtained from your browser.

**_Step 3: Run books scraper_**

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

**_Step 4: Run shelves merger_**

```
python .\shelves_merger.py
```

This script will collect all books, remove duplicates, clean the attributes of the books and clean all reviews.

**_Step 5: Generate Network_**

```
python .\generate_network.py
```

![alt text](https://github.com/2016judea/literature-mutations/blob/master/example-output.PNG)
