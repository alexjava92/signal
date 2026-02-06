const PREFIX = "/signal";

module.exports = async function(eleventyConfig) {
  eleventyConfig.addPassthroughCopy("src/css");
  eleventyConfig.addPassthroughCopy("src/assets");
  eleventyConfig.addPassthroughCopy("src/favicon.svg");

  eleventyConfig.addCollection("posts", function(collectionApi) {
    return collectionApi.getFilteredByGlob("src/posts/*.md").reverse();
  });

  eleventyConfig.addFilter("dateDisplay", function(date) {
    return new Date(date).toLocaleDateString("ru-RU", {
      year: "numeric",
      month: "long",
      day: "numeric"
    });
  });

  eleventyConfig.addFilter("url", function(path) {
    return PREFIX + path;
  });

  eleventyConfig.addFilter("readingTime", function(content) {
    const words = (content || "").split(/\s+/).length;
    const minutes = Math.ceil(words / 200);
    if (minutes === 1) return "1 мин";
    return minutes + " мин";
  });

  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes"
    },
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
    pathPrefix: "/signal/"
  };
};
