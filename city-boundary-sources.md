# City Boundary Data Sources Reference

This file contains the recommended data sources and OSM relation information for all cities in our database, extracted from the City boundary data sources PDF.

## Cities Already Processed (Have Detailed Boundaries)
1. London - OSM
2. New York - OSM 
3. Tokyo - OSM
4. Los Angeles - OSM/US Census
5. Chicago - OSM/US Census
6. Houston - OSM/US Census
7. Phoenix - OSM/US Census
8. Philadelphia - OSM/US Census
9. San Antonio - OSM/US Census
10. San Diego - OSM/US Census
11. San Francisco - OSM/US Census place shapefile
12. Toronto - Statistics Canada digital boundary file
13. Seoul - OSM relation name="서울특별시" or Seoul with admin_level=6/7
14. Vienna - OSM relation name="Wien" with admin_level=8
15. Seattle - OSM/US Census place shapefile
16. Milan - OSM relation name="Milano" with admin_level=8
17. Boston - OSM/US Census place shapefile
18. Vancouver - Statistics Canada digital boundary file
19. Miami - OSM/US Census place shapefile
20. Las Vegas - OSM/US Census place shapefile

## Cities 21-30 (Next Priority - Phase 4)
21. Stockholm - OSM relation name="Stockholm" with admin_level=8
22. Melbourne - OSM relation name="Melbourne" with admin_level=8
23. Oslo - OSM relation name="Oslo" with admin_level=8
24. Munich - OSM relation name="München" with admin_level=8
25. Istanbul - OSM relation name="İstanbul" with admin_level=8
26. Helsinki - OSM relation name="Helsinki" with admin_level=8
27. Atlanta - US Census place shapefile for Atlanta
28. Bangkok - OSM relation name="กรุงเทพมหานคร" with admin_level=6/7
29. Prague - OSM relation name="Praha" with admin_level=8
30. Washington - US Census place shapefile for Washington, DC (District of Columbia)

## Cities 31-40
31. Montreal - Statistics Canada digital boundary file - Census subdivision for Montréal
32. Beijing - OSM relation name="北京市" with admin_level=6/7
33. Orlando - US Census place shapefile for Orlando
34. St. Louis - US Census place shapefile for St. Louis
35. Portland - US Census place shapefile for Portland (Oregon)
36. Dublin - OSM relation name="Dublin" with admin_level=8
37. Osaka - OSM relation name="大阪市" with admin_level=8
38. Denver - US Census place shapefile for Denver
39. Copenhagen - OSM relation name="København" with admin_level=8
40. Auckland - OSM relation name="Auckland" with admin_level=8

## Cities 41-50
41. Frankfurt - OSM relation name="Frankfurt am Main" with admin_level=8
42. Zurich - OSM relation name="Zürich" with admin_level=8
43. Kuala Lumpur - OSM relation name="Kuala Lumpur" with admin_level=8
44. Minneapolis - US Census place shapefile for Minneapolis
45. Ottawa - Statistics Canada digital boundary file - Census subdivision for Ottawa
46. Austin - US Census place shapefile for Austin
47. Calgary - Statistics Canada digital boundary file - Census subdivision for Calgary
48. Dallas - US Census place shapefile for Dallas
49. Brussels - OSM relation name="Bruxelles"/Brussel with admin_level=8
50. Lisbon - OSM relation name="Lisboa" with admin_level=8

## Cities 51-60
51. Honolulu - US Census place shapefile for Honolulu (island of Oʻahu)
52. Detroit - US Census place shapefile for Detroit
53. Krakow - OSM relation name="Kraków" with admin_level=8
54. Shanghai - OSM relation name="上海市" with admin_level=6/7
55. San Jose - US Census place shapefile for San Jose
56. New Orleans - US Census place shapefile for New Orleans
57. Nashville - US Census place shapefile for Nashville–Davidson
58. Edmonton - Statistics Canada digital boundary file - Census subdivision for Edmonton
59. Salt Lake City - US Census place shapefile for Salt Lake City
60. Baltimore - US Census place shapefile for Baltimore

## Cities 61-70
61. Bordeaux - OSM relation name="Bordeaux" with admin_level=8
62. Gothenburg - OSM relation name="Göteborg" with admin_level=8
63. Cleveland - US Census place shapefile for Cleveland
64. Valencia - OSM relation name="València"/Valencia with admin_level=8
65. Glasgow - OSM relation name="Glasgow" with admin_level=8
66. Doha - OSM relation name="Doha" with admin_level=8
67. Warsaw - OSM relation name="Warszawa" with admin_level=8
68. Sao Paulo - OSM relation name="São Paulo" with admin_level=8
69. Taipei - OSM relation name="臺北市"/Taipei with admin_level=6/7
70. Tucson - US Census place shapefile for Tucson

## Cities 71-80
71. Pittsburgh - US Census place shapefile for Pittsburgh
72. Charlotte - US Census place shapefile for Charlotte
73. Lyon - OSM relation name="Lyon" with admin_level=8
74. Nagoya - OSM relation name="名古屋市" with admin_level=8
75. Porto - OSM relation name="Porto" with admin_level=8
76. Perth - OSM relation name="Perth" with admin_level=8
77. Bilbao - OSM relation name="Bilbao" with admin_level=8
78. Cape Town - OSM relation name="Cape Town" with admin_level=8
79. Sapporo - OSM relation name="札幌市" with admin_level=8
80. Athens - OSM relation name="Αθήνα"/Athens with admin_level=8

## Cities 81-90
81. Hamburg - OSM relation name="Hamburg" with admin_level=8
82. Brisbane - OSM relation name="Brisbane" with admin_level=8
83. Tampa - US Census place shapefile for Tampa
84. Naples - OSM relation name="Napoli" with admin_level=8
85. Richmond - US Census place shapefile for Richmond (Virginia)
86. Birmingham - For UK: OSM relation name="Birmingham" with admin_level=8; For Alabama: US Census
87. Raleigh - US Census place shapefile for Raleigh
88. Rochester - US Census place shapefile for Rochester (New York)
89. Hong Kong - OSM relation name="香港特別行政區"/Hong Kong with admin_level=4/5
90. Nantes - OSM relation name="Nantes" with admin_level=8

## Cities 91-101
91. Toulouse - OSM relation name="Toulouse" with admin_level=8
92. Rio de Janeiro - OSM relation name="Rio de Janeiro" with admin_level=8
93. Paris - OSM (processed in basic form)
94. Singapore - OSM (processed in basic form)  
95. Rome - OSM (processed in basic form)
96. Madrid - OSM (processed in basic form)
97. Barcelona - OSM (processed in basic form)
98. Berlin - OSM (processed in basic form)
99. Sydney - OSM (processed in basic form)
100. Amsterdam - OSM relation name="Amsterdam" with admin_level=8
101. (Additional city to be identified)

## Key Data Source Types

### OpenStreetMap (OSM)
- Use Overpass API or polygons.openstreetmap.fr
- Query format: relation["boundary"="administrative"]["admin_level"~"7|8"]["name"="CityName"]
- Most cities use admin_level=8, some Asian cities use 6/7

### US Census Bureau
- TIGER/Line cartographic boundary files (places)
- Download place shapefiles and filter by city name
- Convert to GeoJSON using Mapshaper or ogr2ogr

### Statistics Canada  
- 2021 digital and cartographic boundary files
- Census subdivision level for Canadian cities
- Convert shapefiles to GeoJSON

### National Data Portals
- Some cities have official municipal data portals
- Generally provide higher accuracy but may have access restrictions

## Notes
- All data should be in WGS-84 (EPSG:4326) projection
- Simplify boundaries using Mapshaper to keep files under 2MB
- Municipal boundaries correspond to admin_level 7-8 in Europe, 6-7 in East Asia
- Always verify "city proper" boundaries vs metropolitan regions