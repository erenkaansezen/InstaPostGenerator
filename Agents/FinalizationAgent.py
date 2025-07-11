class FinalizationAgent:
    def finalize(self, title, description, hashtags):
        return f"{title}\n\n{description}\n\n{' '.join(hashtags)}"
