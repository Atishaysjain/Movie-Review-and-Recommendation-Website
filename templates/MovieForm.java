import java.io.*;
import javax.servlet.*;
import javax.servlet.http.*;

public class MovieForm extends HttpServlet {
 
   public void doGet(HttpServletRequest request, HttpServletResponse response)
      throws ServletException, IOException {
      
      response.setContentType("text/html");

      PrintWriter out = response.getWriter();
      String title = "Using GET Method to Read Form Data";
      String docType =
         "<!doctype html public \"-//w3c//dtd html 4.0 " + "transitional//en\">\n";
         
      out.println(docType +
         "<html>\n" +
            "<head><title>" + title + "</title></head>\n" +
            "<body bgcolor = \"#f0f0f0\">\n" +
               "<h1 align = \"center\">" + Movie And Directors + "</h1>\n" +
               "<ul>\n" +
                  "  <li><b>Movie Name</b>: "
                  + request.getParameter("movie_name") + "\n" +
                  "  <li><b>Director Name</b>: "
                  + request.getParameter("director_name") + "\n" +
               "</ul>\n" +
            "</body>" +
         "</html>"
      );
   }
