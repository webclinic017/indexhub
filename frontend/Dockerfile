FROM node:17-alpine

ARG FONTAWESOME_NPM_AUTH_TOKEN

WORKDIR /app

COPY package.json .

RUN npm config set "@fortawesome:registry" https://npm.fontawesome.com/
RUN npm config set "//npm.fontawesome.com/:_authToken" $FONTAWESOME_NPM_AUTH_TOKEN

RUN npm install
RUN mkdir node_modules/.cache && chmod -R 777 node_modules/.cache

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
