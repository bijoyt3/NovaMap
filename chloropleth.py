#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 20:11:33 2021

@author: bijoythomas
"""
import pandas as pd
import numpy as np
import json
from urllib.request import urlopen
import folium

#Extracts values from GeoJson file and outputs into 2 column DataFrame
def prep_df(GeoJsonFile):
   """
        Creates a 2 Column DataFrame from GeoJson file
        
        @param GeoJsonFile: GeoJson file which holds the coordinates for the various shapes (polygons) in your map
        @return 2 column dataframe of City and Zipcode 
    """
    town_count = len(GeoJsonFile["features"])
    
    town = []
    zipcode = []
    
    for i in range(town_count):
        town.append(GeoJsonFile["features"][i]["properties"]['ZIPCITY'])
        zipcode.append(GeoJsonFile["features"][i]["properties"]['ZIPCODE'])
    
    output_list = list(zip(town, zipcode))
    
    output_df = pd.DataFrame(output_list, columns=['Town', 'Zip'])
    
    output_df.drop_duplicates(inplace=True)
    output_df.sort_values(by='Town', inplace=True)
    output_df.reset_index(drop=True, inplace=True)
    
    return output_df

#Merges GeoJson df and Sales df 
def merge_df(df1, filename):
    """
        Ingests sales price Excel file, creates a DataFrame, and merges with GeoJson DataFrame 
        
        @param df1: GeoJson DataFrame
        @param filename: Filepath of Sales Price Excel File
        @return 5 column dataframe of City, Zipcode, Closed Sales, 2011 Avg. Sales Price, 2020 Avg. Sales Price, and Percent Change over period
    """
    #Import file with sales prices
    salesByZip = pd.read_excel(filename)
    
    #Create % Change Column
    salesByZip['Percent Change'] = np.rint(salesByZip.pct_change(axis=1)['2020 Sales Price'] * 100).astype(int)

    #Merge DataFrame
    combined_df = pd.merge(df1, salesByZip, on='Zip')
    
    return combined_df

#Read GeoJson File for Loudoun County
with urlopen('https://opendata.arcgis.com/datasets/71be474fdf00429d98d1adab185c5ec9_1.geojson') as response:
    loco_zips = json.load(response)

#Read GeoJson file for Fairfax County
with urlopen('https://opendata.arcgis.com/datasets/3111976184004077b836f535f31eadf1_21.geojson') as response:
    ffx_zips = json.load(response)

### COMBINE GEOJSONS ###
#Reconcile conflicting ZIPCITY/ZI_TOWN and ZIPCODE/ZI_ZIP keys
for feature in loco_zips['features']:
    feature['properties']['ZIPCITY'] = feature['properties'].pop('ZI_TOWN')
    feature['properties']['ZIPCODE'] = feature['properties'].pop('ZI_ZIP')

#Extract all "features" from Fairfax GeoJson
temp = ffx_zips['features']

#Append Loudoun features to temp variable
for feature in loco_zips['features']:
    temp.append(feature)
 
#Create new dictionary with combined list of features
combined_dict = {}
combined_dict['type'] = "FeatureCollection"
combined_dict['features'] = temp

### LOUDOUN COUNTY DATA PREP ###

#Create Dataframe from GeoJson
loco_zipcodes = prep_df(loco_zips)

#Merge GeoJson df and Sales df
loco_combined_df = merge_df(loco_zipcodes, 'LoCo_AvgSaleByZip.xlsx')

### FAIRFAX COUNTY DATA PREP ###

#Create Dataframe from GeoJson
ffx_zipcodes = prep_df(ffx_zips)

#Merge GeoJson df and Sales df
ffx_combined_df = merge_df(ffx_zipcodes, 'FFX_AvgSaleByZip.xlsx')

### CREATE COMBINED COUNTY DATAFRAME ###
loco_combined_df['County'] = 'LOUDOUN'
ffx_combined_df['County'] = 'FAIRFAX'

final_df = pd.concat([loco_combined_df, ffx_combined_df], axis=0)
final_df.sort_values(by=['County', 'Town'], inplace=True)
final_df.reset_index(drop=True, inplace=True)

#Drop Outlier of Fort Belvoir
final_df.drop(index=28, inplace=True)

# #ADD % CHANGE, NUM. CLOSED SALES, 2011 SALES PRICE, AND 2020 SALES PRICE TO GEOJSON
for feature in combined_dict['features']:

    for index, row in final_df.iterrows():
        if row['Zip'] == feature['properties']['ZIPCODE']:
            feature['properties']['PercentChange'] = str(row['Percent Change']) + "%"
            feature['properties']['ClosedSales'] = row['NumClosedSales']
            feature['properties']['2011AvgPrice'] = "${:,}".format(int(row['2011 Sales Price']))
            feature['properties']['2020AvgPrice'] = "${:,}".format(int(row['2020 Sales Price']))
            break
        else:
            feature['properties']['PercentChange'] = "N/A"
            feature['properties']['ClosedSales'] = "N/A"
            feature['properties']['2011AvgPrice'] = "N/A"
            feature['properties']['2020AvgPrice'] = "N/A"
  
#Create Folium Object 
countyMap = folium.Map(location=[38.948722, -77.5033162], zoom_start=10, tiles='cartodbpositron')

style_function = "font-size: 15px; font-weight: bold"

#Create NoVA Choropleth
nova_choropleth = folium.Choropleth(geo_data=combined_dict,
              data=final_df,
              columns=["Zip", "Percent Change"],
              key_on="feature.properties.ZIPCODE",
              fill_color='RdYlBu',
              fill_opacity=1, 
              line_opacity=1,
              nan_fill_color = 'gray',
              highlight=True,
              legend_name="Percent Change").add_to(countyMap)


#Add tooltip to NoVA choropleth (values come from GeoJson file)
nova_choropleth.geojson.add_child(folium.features.GeoJsonTooltip(
        fields=['ZIPCITY','ZIPCODE', 'PercentChange', '2011AvgPrice', '2020AvgPrice', 'ClosedSales'],
        aliases=['Town:', 'Zip:', '% Change:', 'Avg. Price in 2011:', 'Avg. Price in 2020:', 'Closed Sales:'],
        style=style_function,
        ))


### ADD TITLE TO HTML PAGE
title_text = '% INCREASE OF AVERAGE SALES PRICE OF ATTACHED TOWNHOMES IN LOUDOUN AND FAIRFAX COUNTY FROM 2011-2020'
title_html = '''
             <h3 align="center" style="font-size:16px;font-family:verdana;line-height: -2px;margin-top: 5px"><b>{}</b></h3>
             '''.format(title_text)
             
countyMap.get_root().html.add_child(folium.Element(title_html))


### SAVE FOLIUM OBJECT TO FINAL HTML FILE            
countyMap.save("index.html")


