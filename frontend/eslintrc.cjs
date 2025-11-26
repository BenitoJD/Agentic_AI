module.exports = {
  root: true,
  env: {
    browser: true,
    es2023: true
  },
  extends: [
    "airbnb",
    "airbnb/hooks",
    "airbnb-typescript",
    "plugin:react-hooks/recommended",
    "plugin:react-refresh/recommended",
    "prettier"
  ],
  parserOptions: {
    project: "./tsconfig.json"
  },
  settings: {
    react: {
      version: "detect"
    }
  },
  rules: {
    "react/react-in-jsx-scope": "off",
    "react/jsx-props-no-spreading": "off"
  }
};

