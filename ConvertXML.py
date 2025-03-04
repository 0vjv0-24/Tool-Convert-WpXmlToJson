import xml.etree.ElementTree as ET
import json
from html import unescape
from bs4 import BeautifulSoup

def clean_html(content):
    soup = BeautifulSoup(content, 'html.parser')
    
    # Remove all tags except <p> and <a> with specific href
    for tag in soup.find_all(True):
        if tag.name == 'p':
            # Remove all attributes from <p> tags
            tag.attrs = {}
            continue
        if tag.name == 'a' and tag.has_attr('href'):
            href = tag['href']
            if href.startswith('https://www') and 'segib.org' not in href:
                continue
        tag.unwrap()
    
    return str(soup)

def parse_wordpress_xml(xml_file, max_items=15):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    posts = []

    ns = {
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
        'wp': 'http://wordpress.org/export/1.2/'
    }

    for item in root.findall('.//item')[:max_items]:
        post = {}
        
		 # Extract post ID
        post_id = item.find('.//wp:post_id', ns)
        post['_id'] = post_id.text if post_id is not None else ''

        # Extract post title
        post['title'] = item.find('title').text
        
		 # Extract post modified GMT and split into year, month, day
        post_modified_gmt = item.find('.//wp:post_modified_gmt', ns)
        if post_modified_gmt is not None and post_modified_gmt.text is not None:
            post['anio'] = post_modified_gmt.text[:4]
            post['mes'] = post_modified_gmt.text[5:7]
            post['dia'] = post_modified_gmt.text[8:10]
        else:
            post['anio'] = ''
            post['mes'] = ''
            post['dia'] = ''

        # Extract post content
        content_encoded = item.find('.//content:encoded', ns)
        if content_encoded is not None and content_encoded.text is not None:
            post['content'] = clean_html(unescape(content_encoded.text))
        else:
            post['content'] = ''

        # Extract excerpt
        excerpt_encoded = item.find('.//excerpt:encoded', ns)
        if excerpt_encoded is not None and excerpt_encoded.text is not None:
            post['excerpt'] = clean_html(unescape(excerpt_encoded.text))
        else:
            post['excerpt'] = ''

        # # Extract taxonomies (categories and tags)
        # taxonomies = []
        # for category in item.findall('.//category[@domain="category"]'):
        #     taxonomies.append(category.text)

        # for tag in item.findall('.//category[@domain="post_tag"]'):
        #     taxonomies.append(tag.text)

        # post['taxonomies'] = taxonomies

        # Extract _wpml_import_language_code
        post['idioma'] = None
        for postmeta in item.findall('.//wp:postmeta', ns):
            meta_key = postmeta.find('.//wp:meta_key', ns).text
            if meta_key == '_wpml_import_language_code':
                meta_value = postmeta.find('.//wp:meta_value', ns).text
                post['idioma'] = meta_value
                break

        # Extract post slug
        post_slug = item.find('.//wp:post_name', ns)
        post['slug'] = post_slug.text if post_slug is not None else ''

        posts.append(post)

    return posts

def write_to_json(posts, output_file):
    data = {
        "espanol": {"posts": []},
        "portugues": {"posts": []}
    }

    for post in posts:
        if post['idioma'] == 'es':
            data["espanol"]["posts"].append(post)
        elif post['idioma'] == 'pt-br':
            data["portugues"]["posts"].append(post)

    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    wordpress_xml_file = "Files/2008.xml"
    output_json_file = "Convert/simple.json"

    parsed_posts = parse_wordpress_xml(wordpress_xml_file, max_items=15)
    write_to_json(parsed_posts, output_json_file)

    print("Conversion completed. Posts saved to:", output_json_file)