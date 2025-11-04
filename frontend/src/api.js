import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL;

export const getBooks = async () => axios.get(API_URL);
export const addBook = async (book) => axios.post(API_URL, book);
export const deleteBook = async (id) => axios.delete(API_URL, { data: { id } });
