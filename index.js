console.log("Hello, Wadhifati!");


import { initializeApp } from "firebase/app";
import { getFirestore, collection, addDoc, getDocs, doc, updateDoc, deleteDoc } from "firebase/firestore";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword } from "firebase/auth";


const firebaseConfig = {
  apiKey: "AIzaSyD25zgn8lFvVvUUM_Cd2RczXrF4RAQFAWU",
  authDomain: "wadhifati-db.firebaseapp.com",
  projectId: "wadhifati-db",
  storageBucket: "wadhifati-db.appspot.com",
  messagingSenderId: "119571517839",
  appId: "1:119571517839:web:afed1a123bed072b76fbfa"
};


const app = initializeApp(firebaseConfig);


const db = getFirestore(app);
const auth = getAuth();

console.log("Firebase and Firestore initialized successfully.");


async function addJobListing() {
  try {
    const docRef = await addDoc(collection(db, "jobListings"), {
      title: "Software Developer",
      description: "Responsible for developing and maintaining software applications.",
      location: "Muscat, Oman",
      postedAt: new Date()
    });
    console.log("Document written with ID: ", docRef.id);
  } catch (e) {
    console.error("Error adding document: ", e);
  }
}

addJobListing();


async function getJobListings() {
  const querySnapshot = await getDocs(collection(db, "jobListings"));
  querySnapshot.forEach((doc) => {
    console.log(`${doc.id} => ${doc.data().title}: ${doc.data().description}`);
  });
}

getJobListings();


async function updateJobListing(docId) {
  const docRef = doc(db, "jobListings", docId);
  await updateDoc(docRef, {
    title: "Senior Software Developer"
  });
  console.log("Document updated");
}


async function deleteJobListing(docId) {
  await deleteDoc(doc(db, "jobListings", docId));
  console.log("Document deleted");
}


async function signUp(email, password) {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    console.log('User signed up:', userCredential.user);
  } catch (error) {
    console.error('Error signing up:', error);
  }
}


async function logIn(email, password) {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    console.log('User logged in:', userCredential.user);
  } catch (error) {
    console.error('Error logging in:', error);
  }
}


