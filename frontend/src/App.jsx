import { useState, useEffect } from "react";
import axios from "axios"; // plus pratique pour les appels API

function App() {
  const [books, setBooks] = useState([]);

  useEffect(() => {
    fetchBooks();
  }, []);

  const fetchBooks = async () => {
    try {
      const response = await axios.get("https://<ton-api-id>.execute-api.<region>.amazonaws.com/prod/");
      // selon ton backend, ça peut être response.data.Items
      setBooks(response.data.Items || response.data);
    } catch (error) {
      console.error("Erreur lors du chargement des livres :", error);
    }
  };

  return (
    <div>
      <h1>📚 AnnyBooks</h1>
      <ul>
        {books.map((book) => (
          <li key={book.id}>
            <strong>{book.title}</strong> — {book.author}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
