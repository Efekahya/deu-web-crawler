from wordcloud import WordCloud
from matplotlib import pyplot as plt
import concurrent.futures
from collections import Counter
from bs4 import BeautifulSoup
import networkx as nx
import requests
URL = 'https://www.deu.edu.tr/'
HEADERS = {
    # changing the user agent to avoid 403 error
    'User-Agent': 'My User Agent 1.0',
}

crawledURLs = []
GRAPH = nx.DiGraph()


def getPageContent(url):
    # get the HTML content of the given url
    page = requests.get(url, headers=HEADERS)
    return BeautifulSoup(page.content, 'html.parser')


def filterLinks(links):
    filteredLinks = []
    blockedFileExtensions = [
        'pdf',
        'jpg',
        'jpeg',
        'png',
        'gif',
        'doc',
        'docx',
        'xls',
        'xlsx',
        'ppt',
        'pptx',
        'zip',
        'rar',
        'tar',
        'gz',
        'exe',
        'mp4',
        'login.php'
    ]
    for link in links:
        parsedLink = link.get('href')
        # check if the link is valid internal link and not in the crawledURLs list
        if parsedLink and 'deu.edu.tr' in parsedLink and parsedLink not in crawledURLs and parsedLink not in filteredLinks and not parsedLink.endswith(tuple(blockedFileExtensions)):
            filteredLinks.append(parsedLink)
    return filteredLinks


# get the links from the given HTML content
def getLinks(content):
    if not content:
        return []

    filteredLinks = filterLinks(content.find_all('a'))
    return filteredLinks


def getWords(content):
    words = []
    # extract the text
    text = content.get_text()

    # split the text into tokens
    tokens = text.split()
    for word in tokens:
        # append the word and its frequency
        words.append(word)
    return words


wordsPerUrl = []
wordList = []


def crawl(url, depth):
    if depth == 0:
        return
    content = getPageContent(url)
    crawledURLs.append(url)
    links = getLinks(content)
    words = getWords(content)

    # add the edges to the graph for visualization
    for link in links:
        GRAPH.add_edge(url, link)

    wordCount = Counter(words)

    wordsPerUrl.append({
        'url': url,
        'words': wordCount
    })

    wordList.extend(words)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(crawl, link, depth - 1) for link in links]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f'An error occurred: {str(e)} {url}')


# Crawl the given URL with the given depth
# This will only crawl the "deu.edu.tr" and its subdomains
# Making the depth bigger than 2 will take a lot of time to finish
crawl(URL, 2)


def printDataAsTable(wordsPerUrl):
    HEADERS = ['Word', 'Frequency', 'Page Count',]
    table = []

    # count every word and its url
    count = Counter(wordList).most_common(250)

    # count how much urls has the word in it
    for word, freq in count:
        page_count = 0
        for url in wordsPerUrl:
            if word in url['words']:
                page_count += 1
        table.append([word, freq, page_count])

    plt.axis('off')
    plt.table(cellText=table, colLabels=HEADERS,
              cellLoc='center', loc='center')
    plt.savefig('frequencyTable.jpg', bbox_inches='tight')
    plt.close()


printDataAsTable(wordsPerUrl)


def generateWordCloud():
    count = Counter(wordList)
    wordcloud = WordCloud(width=1920, height=1080,
                          background_color='white').generate_from_frequencies(count)

    wordcloud.to_image().save('wordcloud.jpg', 'JPEG')


generateWordCloud()


def calculateDegreeCentrality():
    degreeCentrality = nx.degree_centrality(GRAPH)
    # sort the dictionary by value in descending order
    sortedDegreeCentrality = sorted(
        degreeCentrality.items(), key=lambda x: x[1], reverse=True)

    return sortedDegreeCentrality


def calculateClosenessCentrality():
    closenessCentrality = nx.closeness_centrality(GRAPH)
    # sort the dictionary by value in descending order
    sortedClosenessCentrality = sorted(
        closenessCentrality.items(), key=lambda x: x[1], reverse=True)

    return sortedClosenessCentrality


def calculateBetweennessCentrality():
    betweennessCentrality = nx.betweenness_centrality(GRAPH)
    # sort the dictionary by value in descending order
    sortedBetweennessCentrality = sorted(
        betweennessCentrality.items(), key=lambda x: x[1], reverse=True)

    return sortedBetweennessCentrality


degreeCentrality = calculateDegreeCentrality()
closenessCentrality = calculateClosenessCentrality()
betweennessCentrality = calculateBetweennessCentrality()


def exportCentralityAsTable(centralityData, filename):
    HEADERS = ['URL', 'Centrality']
    table = []
    # limit to 150
    centrality = centralityData[:150]
    for url, value in centrality:
        table.append([url, value])

    plt.axis('off')
    table = plt.table(cellText=table, colLabels=HEADERS,
                      cellLoc='left', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.5)
    plt.savefig(filename, bbox_inches='tight')
    plt.close()


exportCentralityAsTable(degreeCentrality, 'degreeCentralityTable.jpg')
exportCentralityAsTable(closenessCentrality, 'closenessCentralityTable.jpg')
exportCentralityAsTable(betweennessCentrality,
                        'betweennessCentralityTable.jpg')


def exportCentralityAsGraph(centralityData, filename):
    centrality = centralityData[:50]

    subgraph_closeness = GRAPH.subgraph([url for url, value in centrality])
    pos = nx.spring_layout(subgraph_closeness)
    plt.figure()
    nx.draw_networkx_nodes(subgraph_closeness, pos, node_size=300)
    nx.draw_networkx_edges(subgraph_closeness, pos, alpha=0.1)
    nx.draw_networkx_labels(subgraph_closeness, pos, font_size=8)
    plt.savefig(filename, bbox_inches='tight')
    plt.close()


exportCentralityAsGraph(closenessCentrality, 'closenessCentralityGraph.jpg')
exportCentralityAsGraph(degreeCentrality, 'degreeCentralityGraph.jpg')
exportCentralityAsGraph(betweennessCentrality,
                        'betweennessCentralityGraph.jpg')
