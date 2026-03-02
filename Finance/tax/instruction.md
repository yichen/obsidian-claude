 I'm very happy with the data ingestion for credit card records and Amazon purchase records. Now I need to get into a different area:       
  tax. This folder contains all the files and text documents that I submitted to the CPA in the past years:                                 
  /Users/ychen2/Dropbox/1-Tax/2-prepare. This folder contains the actual filing of those years: /Users/ychen2/Dropbox/1-Tax/3-archive.       
  That is the CPA will take what I provided her that is contained in the prepare folder and she will file the text. The final text           
  filing documents are now in the archive folder.                                                                                            
                                                                                                                                         
  I want you to provide an ingestion system that will ingest from both folders but keep them separate. The ingested file should be saved     
   in a sub folder under ~/Obsidian/Finance/tax. We can decide what is the best format for the ingest. I assume the YAML file provides       
  richer context, But I am open to suggestions. Also I don't know if it makes sense that after ingest should we also include them in the     
   SQLite database? Text documents are very very important for accuracy. We need to have a 100% accuracy guarantee after ingesting each      
  document. You need to verify if the data can be reconciled with what it shows on the appropriate text forms or even the input, even        
  the documents themselves. Provide summaries like totals, sums. This should all be validated when ingesting each single document. We        
  need to provide enough information to the point that you can file tax for me next year.                                                    
                                                                                                                    