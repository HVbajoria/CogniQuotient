import streamlit as st
import subprocess
import warnings
import os
from PIL import Image

st.set_page_config( 
     page_title="CogniQuotient", 
     page_icon="🏫",
     initial_sidebar_state="expanded", 
 ) 
if 'username' not in st.session_state:
    st.session_state["username"]="User"
    
def gradient_text(text, color1, color2):
    gradient_css = f"""
        background: -webkit-linear-gradient(left, {color1}, {color2});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        font-size: 42px;
    """
    return f'<span style="{gradient_css}">{text}</span>'

def gradient_text2(text, color1, color2):
    gradient_css = f"""
        background: -webkit-linear-gradient(left, {color1}, {color2});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 22px;
        font-style: italic;
    """
    return f'<span style="{gradient_css}">{text}</span>'

color1 = "#0d3270"
color2 = "#0fab7b"
text = "Legit Lens"

styled_text = gradient_text(text, color1, color2)
styled_text1 = gradient_text2("A Fake News Detection Tool", color2, color1)

styled_text = gradient_text(text, color1, color2)
st.write(f"<div style='text-align: center;'>{styled_text}</div>", unsafe_allow_html=True)
st.write(f"<div style='text-align: center;'>{styled_text1}</div>", unsafe_allow_html=True)
st.subheader("Weclome "+st.session_state["username"]+" 👋")
# load the model and stuff
@st.cache_resource
def load():
  # useful
  import os
  import math
  import numpy as np
  import pickle
  import requests
  import urllib.request
  import io
  import zipfile
  import warnings

  # html
  from bs4 import BeautifulSoup as bs

  import azure.storage.blob as blob

  # Create a BlobServiceClient object for the storage account.
  blob_service_client = blob.BlobServiceClient.from_connection_string(conn_str=os.environ['AZURE_STORAGE_CONNECTION_STRING'])

  # Get a BlobClient object for the zip file.
  container_client = blob_service_client.get_container_client(container= 'dataset') 

  # download and unzip resources
  for blob in container_client.list_blobs():
    if blob.name == 'data.zip':
      with open(file=blob.name, mode="wb") as download_file:
          download_file.write(container_client.download_blob(blob.name).readall())

      with zipfile.ZipFile('data.zip', 'r') as zipper:
          zipper.extractall()

  with open(os.path.join('.', 'train_val_data.pkl'), 'rb') as f:
      train_data, val_data = pickle.load(f)

  warnings.warn('Data loaded.')

  from sklearn.linear_model import LogisticRegression
  from sklearn.metrics import precision_recall_fscore_support, accuracy_score, confusion_matrix

  # natural language and vocab
  import nltk
  nltk.download('words')
  from nltk.corpus import words
  vocab = words.words()

  y_train = [label for url, html, label in train_data]
  y_val = [label for url, html, label in val_data]

  # prepare data
  def prepare_data(data, featurizer, is_train):
      X = []
      for index, datapoint in enumerate(data):
          url, html, label = datapoint
          html = html.lower()

          features = featurizer(url, html)

          # Gets the keys of the dictionary as descriptions, gets the values as the numerical features.
          feature_descriptions, feature_values = zip(*features.items())

          X.append(feature_values)

      return X, feature_descriptions

  # train model
  def train_model(X_train, y_train):
      model = LogisticRegression(solver='liblinear')
      model.fit(X_train, y_train)

      return model

  # wrapper function for everything above
  def instantiate_model(compiled_featurizer, train_data, val_data):
      X_train, feature_descriptions = prepare_data(train_data, compiled_featurizer, True)
      X_val, _ = prepare_data(val_data, compiled_featurizer, False)

      model = train_model(X_train, y_train)

      return model, X_train, X_val, feature_descriptions

  # a wrapper function that takes in named a list of keyword argument functions
  # each of those functions are given the URL and HTML and expected to return a list or dictionary with the appropriate features
  def create_featurizer(**featurizers):
      def featurizer(url, html):
          features = {}

          for group_name, featurizer in featurizers.items():
              group_features = featurizer(url, html)

              if type(group_features) == type([]):
                  for feature_name, feature_value in zip(range(len(group_features)), group_features):
                      features[group_name + ' [' + str(feature_name) + ']'] = feature_value
              elif type(group_features) == type({}):
                  for feature_name, feature_value in group_features.items():
                      features[group_name + ' [' + feature_name + ']'] = feature_value
              else:
                  features[group_name] = feature_value

          return features

      return featurizer

  # evaluate model
  def evaluate_model(model, X_val, y_val):
      y_val_pred = model.predict(X_val)

      print(print_metrics(y_val, y_val_pred))
      confusion_matrix(y_val, y_val_pred)

      return y_val_pred

  # confusion matrices
  import pandas as pd
  import seaborn as sns
  import matplotlib.pyplot as plt

  def plot_confusion_matrix(y_val, y_val_pred):
      # Create the Confusion Matrix
      cnf_matrix = confusion_matrix(y_val, y_val_pred)

      # Visualizing the Confusion Matrix
      class_names = [0, 1]  # Our diagnosis categories

      fig, ax = plt.subplots()
      # Setting up and visualizing the plot (do not worry about the code below!)
      tick_marks = np.arange(len(class_names))
      plt.xticks(tick_marks, class_names)
      plt.yticks(tick_marks, class_names)
      sns.heatmap(pd.DataFrame(cnf_matrix), annot=True, cmap='YlGnBu', fmt='g')  # Creating heatmap
      ax.xaxis.set_label_position('top')
      plt.tight_layout()
      plt.title('Confusion matrix', y=1.1)
      plt.ylabel('Actual Labels')
      plt.xlabel('Predicted Labels')

  # other metrics
  def print_metrics(y_val, y_val_pred):
      prf = precision_recall_fscore_support(y_val, y_val_pred)
      return {'Accuracy': accuracy_score(y_val, y_val_pred), 'Precision': prf[0][1], 'Recall': prf[1][1],
              'F-1 Score': prf[2][1]}

  # gets the log count of a phrase/keyword in HTML (transforming the phrase/keyword to lowercase).
  def get_normalized_keyword_count(html, keyword):
      # only concern words inside the body, to speed things up
      try:
          necessary_html = html.split('<body')[1].split('</body>')[0]
      except:
          necessary_html = html  # if it doesn't have a body...

      return math.log(1 + necessary_html.count(keyword.lower()))  # log is a good normalizer

  # count the number of words in a URL
  def count_words_in_url(url):
      for i in range(len(url), 2, -1):  # don't count the first letter, because sometimes that might be a word by itself
          if url[:i].lower() in vocab:  # if it's a word
              return 1 + count_words_in_url(url[i:])  # get more words, and keep counting
      return 0  # no words in URL (or at least, it doesn't start with a word, such as NYTimes)

  def url_extension_featurizer(url, html):
      features = {}

      extensions = ['.com', '.org', '.edu', '.net', '.co', '.nz', '.media', '.za', '.fr', '.is', '.tv', '.press',
                    '.news', '.uk', '.info', '.ca', '.agency', '.us', '.ru', '.su', '.biz', '.ir']

      for extension in extensions:
          features[extension] = url.endswith(extension)

      return features

  def keyword_featurizer(url, html):
      features = {}

      keywords = ['vertical', 'news', 'section', 'light', 'data', 'eq', 'medium', 'large', 'ad', 'header', 'text', 'js',
                  'nav', 'analytics', 'article', 'menu', 'tv', 'cnn', 'button', 'icon', 'edition', 'span', 'item', 'label',
                  'link', 'world', 'politics', 'president', 'donald', 'business', 'food', 'tech', 'style', 'amp', 'vr',
                  'watch', 'search', 'list', 'media', 'wrapper', 'div', 'zn', 'card', 'var', 'prod', 'true', 'window', 'new',
                  'color', 'width', 'container', 'mobile', 'fixed', 'flex', 'aria', 'tablet', 'desktop', 'type', 'size',
                  'tracking', 'heading', 'logo', 'svg', 'path', 'fill', 'content', 'ul', 'li', 'shop', 'home', 'static',
                  'wrap', 'main', 'img', 'celebrity', 'lazy', 'image', 'high', 'noscript', 'inner', 'margin', 'headline',
                  'child', 'interest', 'john', 'movies', 'music', 'parents', 'real', 'warren', 'opens', 'share', 'people',
                  'max', 'min', 'state', 'event', 'story', 'click', 'time', 'trump', 'elizabeth', 'year', 'visit', 'post',
                  'public', 'module', 'latest', 'star', 'skip', 'imagesvc', 'posted', 'ltc', 'summer', 'square', 'solid',
                  'default', 'super', 'house', 'pride', 'week', 'america', 'man', 'day', 'wp', 'york', 'id', 'gallery',
                  'inside', 'calls', 'big', 'daughter', 'photo', 'joe', 'deal', 'app', 'special', 'source', 'red', 'table',
                  'money', 'family', 'featured', 'makes', 'pete', 'michael', 'video', 'case', 'says', 'popup', 'carousel',
                  'category', 'script', 'helvetica', 'feature', 'dark', 'extra', 'small', 'horizontal', 'bg', 'hierarchical',
                  'paginated', 'siblings', 'grid', 'active', 'demand', 'background', 'height', 'cn', 'cd', 'src', 'cnnnext',
                  'dam', 'report', 'trade', 'images', 'file', 'huawei', 'mueller', 'impeachment', 'retirement', 'tealium',
                  'col', 'immigration', 'china', 'flag', 'track', 'tariffs', 'sanders', 'staff', 'fn', 'srcset', 'green',
                  'orient', 'iran', 'morning', 'jun', 'debate', 'ocasio', 'cortez', 'voters', 'pelosi', 'barr', 'buttigieg',
                  'american', 'object', 'javascript', 'uppercase', 'omtr', 'chris', 'dn', 'hfs', 'rachel', 'maddow', 'lh',
                  'teasepicture', 'db', 'xl', 'articletitlesection', 'founders', 'mono', 'ttu', 'biden', 'boston', 'bold',
                  'anglerfish', 'jeffrey', 'radius']

      for keyword in keywords:
          features[keyword] = get_normalized_keyword_count(html, keyword)

      return features

  def url_word_count_featurizer(url, html):
      return count_words_in_url(url.split('.')[-2])
      # for example, www.google.com will return google and nytimes.com will return nytimes

  compiled_featurizer = create_featurizer(
      url_extension=url_extension_featurizer,
      keyword=keyword_featurizer,
      url_word_count=url_word_count_featurizer,
      html_length=lambda url, html: len(html),
      url_length=lambda url, html: len(url))

  print('Beginning to train model.')
  model, X_train, X_val, feature_descriptions = instantiate_model(compiled_featurizer, train_data, val_data)
  print('Trained model.')
    
  return model, feature_descriptions, compiled_featurizer, requests, confusion_matrix, print_metrics, train_data, val_data

model, feature_descriptions, compiled_featurizer, requests, confusion_matrix, print_metrics, train_data, val_data = load()

best_matrix = Image.open('confusion_matrix.png')


# on the right side, allow users to submit a URL
st.write('*(Note that we do not use the bag-of-words or GloVe features in this model, in order to speed up deployment and save memory.)*')

with st.form(key='try_it_out'):
  raw_url = st.text_input(label='Enter a news article or site URL to predict validity', key='url')
  st.write('*Make sure your URL is valid.*')

  if st.form_submit_button(label='Submit', type='primary'):
    try:
      if '://' not in raw_url:
        raw_url = 'http://' + raw_url
      
      response = requests.get(raw_url)
      html = response.text.lower()
      url = raw_url.split('/')[2]

      features = compiled_featurizer(url, html)
      warnings.warn(str(features))
      _, feature_values = zip(*features.items())

      prediction = model.predict([feature_values])[0]
      
      st.write('*We predict that your news is ' + ('FAKE' if prediction else 'REAL') + ' news!*')      
      st.divider()
      
      products = [(coef_ * feature_values[index], coef_) for index, coef_ in enumerate(model.coef_[0].tolist())]
      items = sorted(zip(feature_descriptions, products), key=lambda item: (1 if prediction else -1) * item[1][0], reverse=True)
      
      with st.expander('See why.'):
        st.write('The top three features that allowed us to make this decision were: **' + items[0][0] + '**, **' + items[1][0] + '**, and **' + items[2][0] + '**!')
      
      with st.expander('See model parameters.'):
        st.write('The intercept (the value when all features are 0) is: **' + str(model.intercept_[0]) + '**.')
        st.divider()
        st.write('Here are all the feature weights that contributed to the decision.')
        st.write('\n\n'.join(map(lambda feature: f'The feature `{feature[0]}` has a weight of **{feature[1][1]}**. Multiplied by its value gives **{feature[1][0]}**.', items)))
    except:
      advice = st.write('*I don\'t think your URL worked. Please check your spelling or try another.*')

st.image(best_matrix, caption='Confusion matrix.')
st.subheader('Here are some metrics for the most accurate model we trained!')
st.write('**Maximum achieved accuracy:** $0.9029126213592233$')
st.write('**Maximum achieved precision:** $0.8404907975460123$')
st.write('**Maximum achieved recall:** $0.9716312056737588$')
st.write('**Maximum achieved F-1 score:** $0.9013157894736842$')

with st.expander('See our data.'):
  st.write('**Training data (only first 20 rows).**')
  st.table({'URL': [datapoint[0] for datapoint in train_data[:20]], 'HTML (for 100 characters)': [datapoint[1][:100] for datapoint in train_data[:20]], 'Label': ['Fake' if datapoint[2] else 'Real' for datapoint in train_data[:20]]})
  st.write('**Testing data (only first 10 rows).**')
  st.table({'URL': [datapoint[0] for datapoint in val_data[:10]], 'HTML (for 100 characters)': [datapoint[1][:100] for datapoint in val_data[:10]], 'Label': ['Fake' if datapoint[2] else 'Real' for datapoint in val_data[:10]]})

  footer="""<style>

a:hover,  a:active {
color: red;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: white;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p>Developed with ❤️ by Innovation Redefined</p>
</div>
"""
st.markdown(footer,unsafe_allow_html=True)
