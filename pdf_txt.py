import PyPDF2

def pdf_to_text(file):

    pdffile = open(file,'rb')

    pdfReader = PyPDF2.PdfFileReader(pdffile)

    num = pdfReader.numPages

    for i in range(0,num):
        pageobj = pdfReader.getPage(i)
        resulttext = pageobj.extractText()
        newfile = open(r"content.txt", "a")
        newfile.writelines(resulttext)
    
    demo=open("content.txt","r")
    str1=demo.read()
    return str1