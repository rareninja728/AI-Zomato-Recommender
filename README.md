# 🍽️ Zomato AI Recommender

An intelligent restaurant recommendation system that combines a Zomato dataset with Groq LLM to provide personalized dining suggestions with AI-generated explanations.

## ✨ Features

- **🤖 AI-Powered Recommendations**: Uses Groq LLM to generate personalized explanations for each restaurant
- **📍 Location-Based Search**: Find restaurants in specific Bangalore localities
- **🍴 Multi-Cuisine Support**: Search for multiple cuisines simultaneously
- **⭐ Smart Filtering**: Filter by rating, budget, and location
- **🔄 Fallback Strategy**: Always returns at least 3 recommendations with intelligent filter relaxation
- **📊 Duplicate Removal**: Ensures each restaurant appears only once
- **✨ Vibe Matching**: Optional natural language preferences for personalized recommendations

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python with SQLite
- **AI/ML**: Groq LLM (Llama 3.1)
- **Database**: SQLite with Zomato dataset
- **Environment**: Python 3.12+

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- Groq API key (sign up at [console.groq.com](https://console.groq.com))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Getting-started-with-tech-
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Create a `.env` file in the `PHASE 3` directory
   - Add your Groq API key:
     ```
     GROQ_API_KEY=your_groq_api_key_here
     ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

The app will open in your browser at `http://localhost:8501`

## 📁 Project Structure

```
Getting-started-with-tech-/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore file
├── README.md                       # This file
├── PHASE 1/                        # Data processing and database
│   ├── dataset/                    # Data cleaning scripts
│   └── zomato.db                   # SQLite database
├── PHASE 3/                        # Environment configuration
│   └── .env                        # Environment variables
├── PHASE 4/                        # Frontend assets
│   └── frontend/                   # Original frontend files
└── PHASE 5/                        # Backend services
    ├── src/
    │   ├── api/routes.py           # API endpoints
    │   ├── models/schemas.py       # Data models
    │   └── services/
    │       ├── db_service.py       # Database operations
    │       └── llm_service.py      # Groq LLM integration
    └── tests/                      # Test files
```

## 🎯 How to Use

1. **Select Location**: Choose your preferred area in Bangalore
2. **Select Cuisines**: Pick one or multiple cuisines you're interested in
3. **Set Preferences**: Adjust minimum rating and maximum budget
4. **Add Your Vibe** (Optional): Describe your perfect dining experience
5. **Get Recommendations**: Click the button to see AI-powered suggestions

Each recommendation includes:
- Restaurant name and rating
- Location and cuisine type
- Cost for two people
- AI-generated explanation of why it matches your preferences

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `PHASE 3` directory:

```env
GROQ_API_KEY=your_groq_api_key_here
DB_PATH=PHASE 1/zomato.db  # Optional: Custom database path
```

### Database

The application uses a SQLite database (`zomato.db`) containing:
- Restaurant information (name, location, rating, cost, cuisines)
- Pre-processed and cleaned Zomato dataset

## 🌐 Deployment

### Streamlit Cloud Deployment

1. **Push to GitHub**
   ```bash
   git remote add origin <your-github-repo-url>
   git branch -M main
   git push -u origin main
   ```

2. **Deploy to Streamlit**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Select the repository and branch
   - Set main script path to `app.py`
   - Add environment variables in the deployment settings:
     - `GROQ_API_KEY`: Your Groq API key

3. **Advanced Settings** (Optional)
   - Python version: 3.12
   - Hardware: Standard (free tier works fine)

### Local Production Deployment

For local production deployment:

```bash
# Install production dependencies
pip install -r requirements.txt

# Run with production settings
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## 🧠 AI Features

### Smart Fallback Strategy

The system uses a 5-step fallback to ensure you always get recommendations:

1. **Strict Filtering**: Apply all user filters
2. **Relax Cuisine**: Include related cuisines (e.g., bakery → cafe, desserts)
3. **Relax Rating**: Reduce minimum rating by 0.5 points
4. **Local Focus**: Top-rated restaurants in your area
5. **City-wide**: Best restaurants across Bangalore

### Explanation Generation

Each restaurant recommendation includes a personalized explanation generated by Groq LLM using the template:

```
[Restaurant Name] in [Location] is a great match for someone looking for
[Cuisine] cuisine because it serves a variety of [Cuisine foods]
and has a rating of [rating].

With a cost of [price], it fits within your budget.
```

## 🐛 Troubleshooting

### Common Issues

1. **"No restaurants found"**
   - The fallback system should prevent this
   - Check if the database file exists in `PHASE 1/zomato.db`

2. **Groq API errors**
   - Verify your API key is correct in the `.env` file
   - Check your Groq API quota and limits

3. **Database connection errors**
   - Ensure the database file path is correct
   - Check file permissions for the database

4. **Streamlit deployment issues**
   - Verify all dependencies are in `requirements.txt`
   - Check environment variables in deployment settings

### Logs and Debugging

- Streamlit logs are shown in the terminal
- Check browser console for frontend errors
- Database queries are logged for debugging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is for educational purposes. Please ensure you have the right to use the Zomato dataset and comply with Groq's terms of service.

## 🙏 Acknowledgments

- **Zomato**: For the restaurant dataset
- **Groq**: For providing the LLM API
- **Streamlit**: For the amazing web app framework

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Review the code comments for implementation details
3. Open an issue on GitHub with:
   - Error messages
   - Steps to reproduce
   - Your environment details

---

**🍽️ Happy Dining with AI-Powered Recommendations!**
