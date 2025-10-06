import gulp from "gulp";
import dartSass from "sass";
import gulpSass from "gulp-sass";
import browserSyncLib from "browser-sync";

const sass = gulpSass(dartSass);
const browserSync = browserSyncLib.create();

// Rutas
const paths = {
  scss: {
    src: "src/scss/**/*.scss",
    dest: "src/styles/",
  },
  html: {
    src: "public/**/*.html",
  },
  js: {
    src: "src/**/*.jsx",
  },
};

// Compilar SCSS
export function styles() {
  return gulp
    .src("src/scss/main.scss")
    .pipe(sass().on("error", sass.logError))
    .pipe(gulp.dest(paths.scss.dest))
    .pipe(browserSync.stream());
}

// Servidor local + Watch
export function serve() {
  browserSync.init({
    server: {
      baseDir: "./public",
    },
    open: false,
    notify: false,
  });

  gulp.watch(paths.scss.src, styles);
  gulp.watch([paths.html.src, paths.js.src]).on("change", browserSync.reload);
}

// Tarea por defecto
export default gulp.series(styles, serve);
