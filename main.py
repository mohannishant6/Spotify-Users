#!/usr/bin/env python
# coding: utf-8

# ## Spotify User Data- A Dashboard


#importing libaries

import pandas as pd
import numpy as np
from math import pi
from bokeh.io import output_notebook, show, output_file
from bokeh.plotting import figure,gmap
from bokeh.models import ColumnDataSource,LabelSet,GMapOptions,BasicTicker, ColorBar, LinearColorMapper, PrintfTickFormatter
from bokeh.palettes import GnBu3,Category20c
from bokeh.plotting import figure, show
from bokeh.transform import cumsum,transform,jitter
from bokeh.layouts import gridplot, grid
import io
from bokeh.embed import components
# from bokeh.models import HoverTool
from bokeh.models import LinearAxis, Range1d
from bokeh.resources import CDN
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn, Div
from jinja2 import Template

import datetime as dt

#output_notebook()
output_file('dash.html')

#read data
df=pd.read_table('C:\\Users\\nishant\\Downloads\\users.tsv')
df.dropna(inplace=True)

#convert to datetime
df['date'] = pd.to_datetime(df.registered_unixtime,unit='s')

#remove data after '2012-06-30' due to sparsity
df=df[df.date<'2012-06-30']

#make age bins
bins = [df.age.min(),0, 10, 20, 30, 40, 50, 60, df.age.max()+1]
df['age_bin']= pd.cut(df['age'], bins,right=False)
df['age_bin']=df.age_bin.astype(str)

#extract year
df['year']=df.date.dt.year
df['year']=df['year'].astype(str)

#pivot to unstack gender
dfp=df.pivot_table(values='age',index='age_bin',columns='gender',aggfunc='count').reset_index()

#plot1
p1 = figure(title='Males between 20-30 are top Users',y_range=['[-1, 0)', '[0, 10)', '[10, 20)', '[20, 30)', '[30, 40)',
       '[40, 50)', '[50, 60)', '[60, 113)'],plot_width=600, plot_height=350,toolbar_location=None)

p1.hbar_stack(['f','m','n'], y='age_bin', height=0.8,color=GnBu3,source=ColumnDataSource(dfp.to_dict('list')),
             legend_label=[x for x in ['female','male','unspecified']])
p1.y_range.range_padding = 0.0
p1.ygrid.grid_line_color = None
p1.legend.location = "top_right"
p1.axis.minor_tick_line_color = None
p1.outline_line_color = None
p1.xaxis.axis_label = 'Count of Users'
p1.yaxis.axis_label = 'Age'
#              
# show(p1)

#make start and end angles for donut
genders=df.groupby('gender').count().user_id.reset_index()
genders['gender']=['Females','Males','Unspecified']
genders['angle'] = genders['user_id']/genders['user_id'].sum() * 2*pi
genders['color'] = Category20c[len(genders['user_id'])]

#plot 2
p2 = figure(title='Nearly 66% of the Users are Males',plot_height=350,plot_width=600, toolbar_location=None)

p2.annular_wedge(x=0, y=0, inner_radius=0.2, outer_radius=0.4,
                start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                line_color="white", fill_color='color',legend_field='gender',source=genders)
p2.axis.visible=False
p2.grid.grid_line_color = None
# show(p2)

#plot 3
hist, edges = np.histogram(df.playcount.values, bins=[0,10000,20000,30000,40000,50000,60000,70000,80000,90000,100000,2000000])
p3 = figure(plot_height=350,plot_width=600,title='Most (~24000) Users listened to about 10000 tracks', tools='', background_fill_color="#fafafa")
p3.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
       fill_color="navy", line_color="white", alpha=0.5)
p3.y_range.start = 0
p3.x_range.start=0
p3.x_range.end=100000
p3.xaxis.axis_label = 'Play Count'
p3.yaxis.axis_label = 'Users'
p3.grid.grid_line_color="white"
# show(p3)

#plot 4
temp_df=df.groupby(df['date'].dt.to_period('Q'))['user_id'].agg('count').reset_index()
p4 = figure(title="Sign-Up increased exponentially towards end of study period", x_axis_type="datetime", plot_height = 350, plot_width = 600)
p4.xaxis.axis_label = 'Date of Registration'
p4.yaxis.axis_label = 'No of Registrations'
p4.varea(temp_df.date, temp_df.user_id,0,fill_color="purple")
# show(p4)

#plot 5
temp=df[['date']]
temp['day'] = temp[['date']].apply(lambda x: dt.datetime.strftime(x['date'], '%A'), axis=1)
temp['time']=temp.date.dt.time
temp.set_index('date',inplace=True)
DAYS = ['Sunday', 'Saturday', 'Friday', 'Thursday', 'Wednesday', 'Tuesday', 'Monday']
#take only 5000 for clearer chart
source = ColumnDataSource(temp.tail(5000))
p5 = figure(y_range=DAYS, x_axis_type='datetime', plot_height = 350, plot_width = 600,
           title="Most Users Sign Up between 3 PM and 8 PM, Weekends don't make a difference")
p5.circle(x='time', y=jitter('day', width=0.7, range=p5.y_range),  source=source, alpha=.75,size=3,fill_color='cyan',line_color='blue')
p5.xaxis[0].formatter.days = ['Hour %H']
p5.x_range.range_padding = 0
p5.ygrid.grid_line_color = None
# show(p5)

#stack and keep only high userbase countries
temp=df.groupby(['country','year']).count()['user_id'].reset_index()
temp2=temp.pivot_table(values='user_id',columns='year',index='country').fillna(0)
temp2=temp2[temp2.sum(axis=1)>1000]
temp2.reset_index(inplace=True)
temp2 = temp2.set_index('country')
# data.drop('Annual', axis=1, inplace=True)
temp2.columns.name = 'Year'

# reshape to 1D array or rates with a month and year for each row.
dft = pd.DataFrame(temp2.stack(), columns=['rate']).reset_index()
#plot 6
source = ColumnDataSource(dft)
colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
mapper = LinearColorMapper(palette=colors, low=dft.rate.min(), high=dft.rate.max())
p6 = figure(plot_width=600, plot_height=350, title="Highest Sign-Up Rate is seen in the US and Russia towards end of study period",
           x_range=list(temp2.index), y_range=list(reversed(temp2.columns)),
           toolbar_location=None, tools="", x_axis_location="above")

p6.rect(x="country", y="Year", width=1, height=1, source=source,
       line_color=None, fill_color=transform('rate', mapper))

color_bar = ColorBar(color_mapper=mapper, location=(0, 0),
                     ticker=BasicTicker(desired_num_ticks=len(colors)),
                     formatter=PrintfTickFormatter(format="%d%%"))
p6.add_layout(color_bar, 'right')
p6.axis.axis_line_color = None
p6.axis.major_tick_line_color = None
# p6.axis.major_label_text_font_size = "10pt"
p6.axis.major_label_standoff = 0
p6.xaxis.major_label_orientation = 1.0
# show(p6)


#Data Snippet
source = ColumnDataSource(df[['user_id', 'country', 'age', 'gender', 'playcount','date']].tail(10))
columns = [
        TableColumn(field="user_id", title="User ID",width=20),
        TableColumn(field="country", title="Country",width=20),
        TableColumn(field="age", title="Age",width=20),
        TableColumn(field="gender", title="Gender",width=20),
        TableColumn(field="playcount", title="Play Count",width=20),
        TableColumn(field="date", title="Registration", formatter=DateFormatter(format="%m/%d/%Y %H:%M:%S"),width=40)
    ]
data_table = DataTable(source=source, columns=columns, height=350)
# show(data_table)

#Page Headings
div = Div(text="""<h1><center>An Overview of Spotify Users Data</center></h1><br/>
<h3><center>This dashboard gives a bird-eye view of the users who registered for Spotify between 2002 and 2012</center></h3>""",
width=1500, height=150,style={"color":"grey", "font-family":"cambria"})

# show(div)

div2 = Div(text="""<h3><center>Below is a snapshot of the Data</center></h3>""",
width=1500, height=50,style={"color":"grey", "font-family":"cambria"})
# show(div)

#arrange all plots in grid
l = grid([[div],[p1, p5,p6], [p3, p4,p2],[div2],[data_table]])

show(l)