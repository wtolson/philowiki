# PhiloWiki
PhiloWiki tests the assertion by [Randall Munroe (see the alt text)](http://xkcd.com/903/) that:
> Wikipedia trivia: if you take any article, click on the first link in the article text not in parentheses or italics, and then repeat, you will eventually end up at "Philosophy".

## Usage

### Command Line
PhiloWiki can be used on the command line by simply specifying the title of Wikipedia Article you wish to start at. Don't forget to escape characters like parentheses that bash might expand.

For example to find the path from Python (programming language) to Philosophy use the command:

    python philowiki.py Python \(programming language\)

### Python Module
PhiloWiki can also be used as a python module making it easy to conduct your own experiments. Drop philowiki.py in what ever directory you're working in and use <code>import philowiki</code>.

A quick example:

    import philowiki
    
    with philowiki:
      nextLink = philowiki.getNextTitle("Dog")
      print "The first link on the wiki page for Dog is", nextLink

The <code>with</code> statement ensures the cache is saved after you are finished. The cache can also be manually saved with a call to <code>philowiki.saveTitleCache()</code>.
