import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';


class ImagesNewHorizontalSlider extends StatelessWidget {
  const ImagesNewHorizontalSlider({Key? key, required this.images})
      : super(key: key);

  final List<String> images;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 175,
      width: double.infinity,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: List.generate(
          images.length,
              (index) {
            return GestureDetector(
              onTap: () {
                context.push('/image', extra: images);
              },
              child: Padding(
                padding: const EdgeInsets.only(left: 23.3),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(12.0),
                  child: Image.network(
                    images[index],
                    height: 175,
                    width: 296.25,
                    fit: BoxFit.cover,
                  ),
                ),
              ),
            );
          },
        )..add(
          const SizedBox(width: 18),
        ), // Right padding for the outermost element
      ),
    );
  }
}
