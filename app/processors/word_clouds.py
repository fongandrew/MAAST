import xmlrpclib
import zlib
from xml.dom.minidom import Document

"""
find frequent words by years or months from the databases
create an xml file that contains the frequent words and put it in the static folder
""" 

#example should be a dictionary
def word_clouds(user_tags = None, user_shape="heart", user_shape_ratio = 1, user_font = "Linux Libertine Regular", user_colors = ['000000']):
  #find frequent words by years or months from the database
  
  # Create the minidom document
  doc = Document()
  
  tagul = doc.createElement("tagul")
  doc.appendChild(tagul)
    
  #head part    
  head = doc.createElement("head")
  tagul.appendChild(head)

  #set the shape
  """
    shape types list:
    cloud
    heart
    star
    triangle
    pentagram
    circle
    rectangle
  """
  shape = doc.createElement("shape")
  shape.setAttribute("type", user_shape)
  shape.setAttribute("angle", "0")
  shape.setAttribute("ratio", str(user_shape_ratio))
  head.appendChild(shape)
  
  #set the font
  """
  <!-- fonts list: 
  <font>BPreplay Bold/>
  <font>BPreplay Bold Italic</font>
  <font>BPreplay Italic</font>
  <font>BPreplay Regular</font>
  <font>Breip Medium</font>
  <font>Duality Regular</font>
  <font>Goudy Bookletter 1911 Regular</font>
  <font>Gunplay Regular</font>
  <font>Heuristica Bold</font>
  <font>Heuristica BoldItalic</font>
  <font>Heuristica Italic</font>
  <font>Heuristica Regular</font>
  <font>League Gothic Regular</font>
  <font>Linux Biolinum Bold</font>
  <font>Linux Biolinum Regular</font>
  <font>Linux Libertine Bold</font>
  <font>Linux Libertine Bold Italic</font>
  <font>Linux Libertine C Regular</font>
  <font>Linux Libertine Italic</font>
  <font>Linux Libertine Regular</font>
  <font>Loved by the King Regular</font>
  <font>Mail Ray Stuff Regular</font>
  <font>Teen bold</font>
  <font>Teen bold Italic</font>
  <font>Teen Italic</font>
  <font>Teen Regular</font>
  <font>TeX Gyre Bonum Bold</font>
  <font>TeX Gyre Bonum Bold Italic</font>
  <font>TeX Gyre Bonum Italic</font>
  <font>TeX Gyre Bonum Regular</font>-->  
  """
  fonts = doc.createElement("fonts")
  font = doc.createElement("font")
  font_text = doc.createTextNode(user_font)
  font.appendChild(font_text)
  fonts.appendChild(font)
  head.appendChild(fonts)

  colors = doc.createElement("colors")
  for user_color in user_colors:
    color = doc.createElement("color")
    color_text = doc.createTextNode(user_color)
    color.appendChild(color_text)
    colors.appendChild(color)
    
  head.appendChild(colors)

  #tag part    
  tags = doc.createElement("tags")
  tagul.appendChild(tags)
    
  #put each tag here
  for word, w in user_tags.iteritems():
    tag = doc.createElement("tag")
    tag.setAttribute("weight", str(w))  
    tags.appendChild(tag)
    tag_text = doc.createTextNode(word)
    tag.appendChild(tag_text)
   
  #To-Do: finish createCloudSVg 
  print doc.toprettyxml()
  createCloudSvg(doc.toprettyxml())
  #create an xml file that contain the frequent words 
#  f = open('cloudAPI.xml', 'w')
#  doc.writexml(f)
#  f.close()
  


def createCloudSvg(cloudAPIxml):
  #create XML-RPC client instance connected to Tagul
  xmlrpcClient = xmlrpclib.ServerProxy('https://tagul.com:4433/api')
  
  cloud = xmlrpcClient.generateCloud (
  	{
  		'userName': 'monica@ischool.berkeley.edu',
  		'apiKey': 'leeHaiva3ahFoo2oothaePohn'
  	},
  	cloudAPIxml
  )


if __name__ == "__main__":
  word_clouds({'Travis':25 , 'Andrew':30})