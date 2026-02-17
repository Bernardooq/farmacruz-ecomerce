import gulp from "gulp";
import dartSass from "sass";
import gulpSass from "gulp-sass";

const sass = gulpSass(dartSass);

// Rutas
const paths = {
  scss: {
    src: "src/styles/**/*.scss",
    dest: "src/styles/dist/",
  },
};

// Compilar SCSS a CSS
export function styles() {
  return gulp
    .src("src/styles/main.scss") // Archivo principal (Atomic Design)
    .pipe(sass().on("error", sass.logError))
    .pipe(gulp.dest(paths.scss.dest));
}

// Watch (escucha cambios y recompila)
export function watchFiles() {
  gulp.watch(paths.scss.src, styles);
}

// Tarea por defecto
export default gulp.series(styles, watchFiles);
