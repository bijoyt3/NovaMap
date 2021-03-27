# NovaMap
This script uses 2 GeoJson files (one for Fairfax county and one for Loudoun county) as well as historical sales prices of townhomes by zipcode to create an interactive choropleth map of percent increase of average sales prices in Northern VA by zipcode. The completed visual is hosted on www.bijoyt.com/novamap. 

![NoVA Choropleth][/Users/bijoythomas/Desktop/Screenshots/Choropleth_Screenshot.png]

## Libraries
I used the folium library to develop the choropleth visualization. 

```
pip install folium
```

The library offers the user several formatting options for the visualizing your charts as well as options for varying degrees of interactivity. There was a very helpful method to output the finished visualization into an .html file as a local copy which made it extremely easy to upload onto my website. 

## Acknowledgements
Leaned on the folium documentation heavily - https://python-visualization.github.io/folium/

## License
This project is licensed under the MIT License - see the LICENSE.md file for details
