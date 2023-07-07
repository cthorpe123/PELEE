#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import uproot
import matplotlib
import matplotlib.pyplot as plt


# In[2]:


ur_data = uproot.open('/uboone/app/users/cthorpe/IonAnalysis/genie_testing/INCLPP/GENIEEvents_BNB_numu.root')['gst']


# In[3]:


query = "pdgf[0] == 2212"


# In[13]:


variables = ur_data.pandas.df(['cc','nc','Ei'])


# In[15]:


print(variables)


# In[16]:


highE = variables.query('Ei > 0.5 and Ei < 20')


# In[17]:


#print(highE)
E = highE['Ei']
#print(E)


# In[18]:


aE = E.to_numpy()
print(aE)


# In[19]:


Edata, Ebin_edges = np.histogram(aE,bins=100)


# In[20]:


fig, ax = plt.subplots()
ax.bar(Ebin_edges[:-1], Edata, width=np.diff(Ebin_edges), edgecolor="black", align="edge")
#plt.show()


# In[ ]:





# In[ ]:




